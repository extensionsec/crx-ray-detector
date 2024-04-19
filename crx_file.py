from io import BufferedReader, BytesIO, TextIOWrapper
import os
from typing import IO, Optional
from zipfile import BadZipFile, ZipFile
from hashlib import md5
from pathlib import Path
from dataclasses import dataclass
from crx3_pb2 import CrxFileHeader, SignedData
import struct


DEFAULT_FILTER_LIST = [
    "html", "css", "js", "json"
]


@dataclass
class CrxResource:
    repository_path: str
    content: Optional[IO[bytes]] = None


@dataclass
class CrxData:
    extension_id: str
    path: Path
    resources: list[CrxResource]


class BadCrx(Exception):
    pass


class CrxFile:

    DIGEST_BUFFER = 65536  # 64kb
    MAGIC_NUMBER = "Cr24"

    HEX_TO_ALPHABET = {
        # Mapping of hexadecimal characters to 'a'-'p' range
        '0': 'a', '1': 'b', '2': 'c', '3': 'd', '4': 'e', '5': 'f', '6': 'g', 
        '7': 'h', '8': 'i', '9': 'j', 'a': 'k', 'b': 'l', 'c': 'm', 'd': 'n',
        'e': 'o', 'f': 'p'
    }

    def __init__(self, crx_path: Path, filter_list: Optional[list[str]] = None,
                    unpack_headers: Optional[bool] = True):
        
        assert crx_path.exists()
        self.path = crx_path
        self.crx_version: Optional[int] = None
        self._header_length: Optional[int] = None
        self._file_buffer: Optional[BufferedReader] = None
        
        self.is_setup = False
        self.is_corrupted = False
        self.reader: BufferedReader = None

        self.rsa_proof: tuple[bytes, bytes] = None
        self.digest: str = None
        
        self.should_unpack_headers = unpack_headers
        self.header: Optional[CrxFileHeader] = None
        self.extension_id: Optional[str] = None
        self.resources: list[CrxResource] = None
        self.filter_list: Optional[list[str]] = filter_list


    def __enter__(self) -> BufferedReader:
        """Opens the file buffer in byte format."""
        if self._file_buffer is None:
            # Just read, never write onto a CRX file
            self._file_buffer = open(self.path, "rb")

        return self._file_buffer
    

    def __exit__(self, *exception_args) -> bool:
        """Closes the file buffer without raised exceptions."""
        if self._file_buffer is not None:
            self._file_buffer.close()
            self._file_buffer = None

        return False  # Do not suppress raised exceptions


    @property
    def header_length(self) -> Optional[int]:
        if not self.is_setup:
            self.setup(setup_resources=False)
        
        return self._header_length
    
        
    @header_length.setter
    def header_length(self, length_bytes: bytes):
        self.header_length = self.little_endian_to_int(length_bytes)
    

    def compute_digest(self) -> str:
        hasher = md5()
        with open(self.path, "rb") as file_bytes:
            while True:
                block = file_bytes.read(self.DIGEST_BUFFER)
                if not block:
                    break
                hasher.update(block)
        return hasher.hexdigest()


    def setup(self, setup_resources: Optional[bool] = True,
                force_setup: Optional[bool] = False) -> None:
        
        def assert_magic_number(buffer: BufferedReader) -> None:
            """Checks the magic number in the initial CRX header bytes."""
            crx_bytes = buffer.read(4)

            magic_number = crx_bytes.decode("utf-8")
            if magic_number != "Cr24":
                raise BadCrx(f"'Unexpected magic number: {magic_number}.")
            
        def get_crx_version(buffer: BufferedReader) -> int:
            """Returns the CRX header's protocol version."""
            version_bytes = buffer.read(4)
            return self.little_endian_to_int(version_bytes)

        if self.is_setup and not force_setup: return

        self.digest = self.compute_digest()

        self._file_buffer = None  # reset the file buffer
        with self as crx_buffer:
            assert_magic_number(crx_buffer)
            self.crx_version = get_crx_version(crx_buffer)
            self._route_crx_setup(self.crx_version, crx_buffer)
            if setup_resources:
                self.setup_resources()
            self.is_setup = True


    def _route_crx_setup(self, crx_version, file_buffer):
        if crx_version == 3:
            self.setup_crx3(file_buffer)
        elif crx_version == 2:
            self.setup_crx2(file_buffer)
        else:
            raise NotImplementedError(f"Unknown version: {crx_version}")


    def setup_crx2(self, buffer: BufferedReader) -> None:
        if not self.should_unpack_headers: return self.strip_crx2(buffer)

        public_key_length_bytes = buffer.read(4)
        signature_length_bytes = buffer.read(4)

        public_key_length = self.little_endian_to_int(public_key_length_bytes)
        signature_length = self.little_endian_to_int(signature_length_bytes)
        self.rsa_proof = (
            buffer.read(public_key_length),
            buffer.read(signature_length)
        )
        

    def decode_extension_id(self, extension_id: bytes):
            # Convert bytes to hexadecimal
            hex_representation = extension_id.hex()

            # Map each hexadecimal character to 'a'-'p'
            return ''.join(
                self.HEX_TO_ALPHABET[char] 
                for char in hex_representation
            )


    def setup_crx3(self, buffer: BufferedReader) -> None:
        if not self.should_unpack_headers: return self.strip_crx3(buffer)

        header_length_bytes = buffer.read(4)
        header_length = self.little_endian_to_int(header_length_bytes)
        header_bytes = buffer.read(header_length)
        self.header = CrxFileHeader()
        self.header.ParseFromString(header_bytes)

        signed_data = SignedData()
        signed_data.ParseFromString(self.header.signed_header_data)
        self.extension_id = self.decode_extension_id(signed_data.crx_id)
        self.rsa_proof = self.header.sha256_with_rsa
        self.ecdsa_proof = self.header.sha256_with_ecdsa

        self.is_setup = True


    @property
    def header_details(self) -> Optional[tuple]:
        if not self.should_unpack_headers: return None
        
        if not self.is_setup: self.setup()
        
        return (self.path, self.crx_version, self.extension_id, self.rsa_proof,
                self.ecdsa_proof)


    @staticmethod
    def little_endian_to_int(bytes_: bytes) -> int:
        """Converts bytes encoded in little-endian to integer."""
        byte_array = bytearray(bytes_)
        result = 0
    
        result += byte_array[0] << 0
        result += byte_array[1] << 8
        result += byte_array[2] << 16
        result += byte_array[3] << 24
        return result & 0xFFFFFFFF
    

    def get_zip_archive(self) -> Optional[ZipFile]:
        # Initial setup is necessary to remove the CRX headers 
        if not self.is_setup:
            # Setup without resources to avoid infinite loop caused by
            # self.setup_resources()
            self.setup(setup_resources=False)

        with self as zip_buffer:
            try:
                zip_file = ZipFile(BytesIO(zip_buffer.read()))

            except (BadZipFile, BadCrx):
                self.is_corrupted = True
                return None

        self.is_corrupted = False
        return zip_file
    
    @staticmethod
    def strip_crx2(crx_file: BufferedReader) -> None:
        public_key_length_bytes = crx_file.read(4)
        signature_length_bytes = crx_file.read(4)

        public_key_length = struct.unpack("<I", public_key_length_bytes)[0]
        signature_length = struct.unpack("<I", signature_length_bytes)[0]

        crx_file.seek(public_key_length, signature_length, os.SEEK_CUR)

    @staticmethod
    def strip_crx3(crx_file: BufferedReader) -> None:
        header_length_bytes = crx_file.read(4)
        header_length = struct.unpack("<I", header_length_bytes)[0]

        crx_file.seek(header_length, os.SEEK_CUR)

        
    def setup_resources(self) -> None:

        zip_archive = self.get_zip_archive()
        if zip_archive is None:
            raise BadCrx("Could not identify the ZIP archive.")
        
        self.resources: list[CrxResource] = []
        for resource_info in zip_archive.infolist():
            if resource_info.is_dir(): continue
            
            filename = resource_info.filename
            resource = CrxResource(filename)
            if (self.filter_list is None
                or filename.split(".")[-1] in self.filter_list):
                # If there is no filter list specified or the extension of the
                # resource file is in the filter list, store its content
                resource.content = zip_archive.open(resource_info)

            self.resources.append(resource)
