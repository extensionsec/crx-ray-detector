import re
from typing import Optional, Self
import yaml
from pathlib import Path
from pprint import pprint


cwd = Path(__file__).parent
configuration_path = cwd.joinpath("configuration.yml")
with open(configuration_path, "r") as configuraiton_file:
    configuration_dict = yaml.safe_load(configuraiton_file)

assert configuration_dict is not None


class ApiKeyPattern:

    def __init__(self, service_name, pattern, keywords=None,
                    sub_services=None):
        self.service_name = "Unknown" if service_name is None else service_name
        self.expression = re.compile(pattern) if pattern is not None else None
        self.keywords: list[str] = keywords if keywords is not None else []
        self.sub_services: list[Self] = \
            sub_services if sub_services is not None else []

    @property
    def pattern(self) -> str:
        if self.expression is None:
            return None
        return self.expression.pattern
    
    @pattern.setter
    def pattern(self, value) -> None:
        self.expression = re.compile(value)
    
    def __repr__(self) -> str:
        return str(self.__dict__)
    
    def check_all_keywords(self, content) -> bool:
        if len(self.keywords) == 0:
            return True
        for keyword in self.keywords:
            if keyword not in content:
                return False
        return True

    def check_any_keyword(self, content) -> bool:
        if len(self.keywords) == 0:
            return True
        for keyword in self.keywords:
            if keyword in content:
                return True
        return False
    
    def match_subservices(self, match_string: str,
                            content: str) -> Optional[str]:
        for service in self.sub_services:
            if service.expression.match(match_string) is None:
                continue
            matches = service.find_matches_with_context(content,
                                                        context_length=0)
            if len(matches) > 0:
                return service.service_name

        return None
    
    def find_matches_with_context(
            self, content: str, context_length=250) -> list[(str, str, str)]:
        if not self.check_any_keyword(content):
            return []
        
        found_matches = self.expression.finditer(content)
        matches_with_context: list[(str, str)] = []

        for result in found_matches:
            match_string = \
                result.group(1) if result.groups() else result.group(0)
            
            start_index = max(0, result.start() - context_length)
            end_index = min(len(content), result.end() + context_length)
            context_before = content[start_index:result.start()]
            context_after = content[result.end():end_index]
            service_name = self.match_subservices(match_string, content)

            matches_with_context.append((
                service_name if service_name is not None else self.service_name,
                match_string, 
                context_before + result.group(0) + context_after
            ))

        return matches_with_context
    
    @classmethod
    def parse_service(cls, service_name, service_data: dict|str) -> Self:
        if isinstance(service_data, str):
            return cls(service_name, service_data)
        elif isinstance(service_data, dict):
            pattern = service_data.get("pattern")
            keywords = service_data.get("keywords")
            if isinstance(keywords, str):
                keywords = [keywords]
            sub_services: list[Self] = []
            if service_data.get("subservices") is not None:
                for sub_name, sub_data in service_data["subservices"].items():
                    full_name = service_name + sub_name
                    sub_service = cls.parse_service(full_name, sub_data)
                    if sub_service.pattern is None:
                        sub_service.pattern = pattern
                    sub_services.append(sub_service)
            return cls(service_name, pattern, keywords, sub_services)
    
    @classmethod
    def parse_configuration(cls, configuration: dict) -> list[Self]:
        api_services: list[Self] = []
        for service_name, service_data in configuration["strict"].items():
            api_services.append(
                cls.parse_service(service_name, service_data)
            )

        broad_services: list[Self] = []
        for (service_name,
                service_data) in configuration["broad"]["services"].items():
            broad_services.append(
                cls.parse_service(service_name, service_data)
            )

        for pattern in configuration["broad"]["patterns"]:
            service = cls(None, pattern)
            service.sub_services = broad_services
            for sub_service in broad_services:
                service.keywords.extend(sub_service.keywords)
            api_services.append(service)

        return api_services


API_PATTERNS = ApiKeyPattern.parse_configuration(
    configuration_dict["service_patterns"])

if __name__ == "__main__":
    # Print the configuration
    for pattern in API_PATTERNS:
        pprint(pattern)