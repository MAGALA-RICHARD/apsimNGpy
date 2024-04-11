crop_codes = {
    1: "Maize",
    2: 'Maize, Soybean',
    3: 'Maize, Wheat',
    4: 'Maize, Wheat, Soybean, Wheat, Maize',
    5: 'TropicalPasture'
}
from abc import ABC, abstractmethod
class ConfigurationManager(ABC):
    def __init__(self, crop_code= None, report_names= None):
        self.crop_codes = crop_codes if not crop_code else crop_codes
        self.report_names = report_names
    @abstractmethod
    def get_config(self):
        pass
