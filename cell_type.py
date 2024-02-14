from abc import ABC, ABCMeta, abstractmethod
import numpy as np

from cell_body import CellBody

class CellTypeAttributesMeta(ABCMeta):
    cell_type_attributes = [
        'seed_radius', 
        'mean_cyc_len', 
        'std_dev_cyc_len',
        'does_age', 
        'lifespan'
    ]

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        for attr in cls.cell_type_attributes:
            if not hasattr(instance, attr):
                raise NotImplementedError(f"Missing required class attribute: {attr}")
        return instance
    

class AbstractCellType(ABC, metaclass=CellTypeAttributesMeta):
    seed_radius: float
    mean_cyc_len: float
    std_dev_cyc_len: float
    does_age: bool
    lifespan: int

    def __init__(cls, self, pos):
        self.cell_body = CellBody(pos, cls.seed_radius)
        
        self.seed_vol = 4.0/3.0 * np.pi * cls.seed_radius**3
        self.current_vol = self.seed_vol
        self.cyc_len = self.get_cyc_len()
        self.g1_len = self.get_g1_len()
        self.current_phase = "G1"
        self.current_cyc_iteration = 0
        self.current_age = 0
        self.is_dead = False

    def get_cyc_len(cls, self):
        return int(np.random.normal(loc=cls.mean_cyc_len, scale=cls.std_dev_cyc_len, size=1))
    
    def get_g1_len(self):
        mean = self.cyc_len / 2.0
        return int(np.random.normal(loc=mean, scale=mean/10.0, size=1))
    
    @abstractmethod
    def do_cell_cycle(self):
        pass

    @abstractmethod
    def g1_phase(self):
        pass

    @abstractmethod
    def g0_phase(self):
        pass

    @abstractmethod
    def s_phase(self):
        pass

    @abstractmethod
    def g2_phase(self):
        pass

    @abstractmethod
    def m_phase(self):
        pass

    @abstractmethod
    def migrate(self):
        pass

    @abstractmethod
    def hypoxic_death(self):
        pass


class GenericCell(AbstractCellType):
    seed_radius = 10.0
    mean_cyc_len = 24.0
    std_dev_cyc_len = 1.0
    does_age = True
    lifespan = 4

    g0_oxy_threshold = 0.5
    hypoxia_theshold = 0.25

    def __init__(self):
        super().__init__()

    def do_cell_cycle(self):
        if self.current_phase == "G0":
            self.g0_phase()
        elif self.current_phase == "G1":
            self.g1_phase()
        elif self.current_phase == "S":
            self.s_phase()
        else:
            self.m_phase()

    def g1_phase(self):
        self.current_cyc_iteration += 1
        
        self.current_vol += self.seed_vol / self.g1_len
        self.cell_body.change_vol(self.current_vol)
        
        if self.current_cyc_iteration == self.g1_len:
            if self.cell_body.get_substance_level("oxygen") < self.g0_oxy_threshold or self.cell_body.is_contact_inhibited():
                self.current_phase = "G0"
            else:
                self.current_phase = "S"

    def g0_phase(self):
        if not self.cell_body.is_contact_inhibited() and self.cell_body.get_substance_level("oxygen") > self.g0_oxy_threshold:
            if self.current_cyc_iteration == self.g1_len:
                self.current_phase = "S"
            else:
                self.current_phase = "M"

    def s_phase(self):
        self.current_cyc_iteration += 1
        if self.current_cyc_iteration == self.cyc_len - 1:
            if self.cell_body.get_substance_level("oxygen") < self.g0_oxy_threshold or self.cell_body.is_contact_inhibited:
                self.current_phase = "G0"
            else:
                self.current_phase = "M"

    def g2_phase(self):
        pass

    def m_phase(self):
        self.cell_body.change_volume(self.seed_vol)
        # !!!! seed new cell where there is space
        self.current_cyc_iteration = 0
        self.cyc_len = self.get_cyc_len()
        self.g1_len = self.get_g1_len()
        if self.does_age:
            self.current_age += 1
        if self.current_age > self.lifespan:
            self.is_dead = True

    def migrate(self):
        pass

    def hypoxic_death(self):
        if self.cell_body.get_substance_level("oxygen") < self.hypoxia_theshold:
            self.is_dead = True