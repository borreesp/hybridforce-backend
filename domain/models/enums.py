from enum import Enum


class AthleteLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermedio"
    RX = "RX"
    HYROX_COMPETITOR = "HYROX Competitor"


class IntensityLevel(str, Enum):
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"


class EnergyDomain(str, Enum):
    AEROBIC = "Aeróbico"
    ANAEROBIC = "Anaeróbico"
    MIXED = "Mixto"


class PhysicalCapacity(str, Enum):
    STRENGTH = "Fuerza"
    ENDURANCE = "Resistencia"
    SPEED = "Velocidad"
    GYMNASTICS = "Gimnásticos"
    METCON = "Metcon"
    MUSCULAR_LOAD = "Carga muscular"


class MuscleGroup(str, Enum):
    LEGS = "Piernas"
    CORE = "Core"
    SHOULDERS = "Hombros"
    POSTERIOR = "Posterior"
    GRIP = "Grip"
    CHEST = "Pecho"
    ARMS = "Brazos"


class HyroxStation(str, Enum):
    SKIERG = "SkiErg"
    SLED_PUSH = "Sled Push"
    SLED_PULL = "Sled Pull"
    FARMERS_CARRY = "Farmers Carry"
    BURPEE_BROAD_JUMP = "Burpee Broad Jump"
    ROW = "Row"
    SANDBAG_LUNGES = "Sandbag Lunges"
    WALL_BALLS = "Wall Balls"
