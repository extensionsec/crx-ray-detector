from io import BufferedReader, BytesIO, TextIOWrapper
import os
from typing import IO, Optional
from zipfile import BadZipFile, ZipFile
from hashlib import md5
from pathlib import Path
from dataclasses import dataclass
import struct


DEFAULT_FILTER_LIST = [
    "html", "css", "js", "json"
]


@dataclass
class XpiResource:
    repository_path: str
    content: Optional[IO[bytes]] = None


@dataclass
class XpiData:
    extension_id: str
    path: Path
    resources: list[XpiResource]


class BadXpi(Exception):
    pass


class XpiFile:

    DIGEST_BUFFER = 65536  # 64kb

    def __init__(self, xpi_path: Path, filter_list: Optional[list[str]] = None):
        
        assert xpi_path.exists()
        self.path = xpi_path
        self.xpi_version: Optional[int] = Path(xpi_path).parent.name  # TODO: 只是为了简化
        self._file_buffer: Optional[BufferedReader] = None
        
        self.is_corrupted = False
        self.reader: BufferedReader = None
        
        self.extension_id: Optional[str] = Path(xpi_path).parent.parent.name  # TODO：得到extension_id
        self.resources: list[XpiResource] = None
        self.filter_list: Optional[list[str]] = filter_list


    def __enter__(self) -> BufferedReader:
        """Opens the file buffer in byte format."""
        if self._file_buffer is None:
            # Just read, never write onto a xpi file
            self._file_buffer = open(self.path, "rb")

        return self._file_buffer
    

    def __exit__(self, *exception_args) -> bool:
        """Closes the file buffer without raised exceptions."""
        if self._file_buffer is not None:
            self._file_buffer.close()
            self._file_buffer = None

        return False  # Do not suppress raised exceptions
    

    def setup(self, setup_resources: Optional[bool] = True) -> None:
        
        self._file_buffer = None  # reset the file buffer
        if setup_resources:
            self.setup_resources()


    def get_zip_archive(self) -> Optional[ZipFile]:
        with self as zip_buffer:
            try:
                zip_file = ZipFile(BytesIO(zip_buffer.read()))

            except (BadZipFile, BadXpi):
                self.is_corrupted = True
                return None

        self.is_corrupted = False
        return zip_file
        
    def setup_resources(self) -> None:

        zip_archive = self.get_zip_archive()
        if zip_archive is None:
            raise BadXpi("Could not identify the ZIP archive.")
        
        self.resources: list[XpiResource] = []
        for resource_info in zip_archive.infolist():
            if resource_info.is_dir(): continue
            
            filename = resource_info.filename
            resource = XpiResource(filename)
            if (self.filter_list is None
                or filename.split(".")[-1] in self.filter_list):
                # If there is no filter list specified or the extension of the
                # resource file is in the filter list, store its content
                resource.content = zip_archive.open(resource_info)

            self.resources.append(resource)