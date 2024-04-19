# -*- coding: utf-8 -*-
"""Generated protocol buffer code."""
from google.protobuf import descriptor as protobuf_descriptor
from google.protobuf import descriptor_pool as protobuf_descriptor_pool
from google.protobuf import symbol_database as protobuf_symbol_database
from google.protobuf.internal import builder as protobuf_builder

# @@protoc_insertion_point(imports)

symbol_database = protobuf_symbol_database.Default()
descriptor_pool = protobuf_descriptor_pool.Default()

# Serialized protobuf file content
serialized_proto = b'\n\ncrx3.proto\x12\x08\x63rx_file\"\xb7\x01\n\rCrxFileHeader\x12\x35\n\x0fsha256_with_rsa\x18\x02 ' \
                   b'\x03(\x0b\x32\x1c.crx_file.AsymmetricKeyProof\x12\x37\n\x11sha256_with_ecdsa\x18\x03 \x03(' \
                   b'\x0b\x32\x1c.crx_file.AsymmetricKeyProof\x12\x19\n\x11verified_contents\x18\x04 \x01(' \
                   b'\x0c\x12\x1b\n\x12signed_header_data\x18\x90N \x01(\x0c\";\n\x12\x41symmetricKeyProof\x12\x12' \
                   b'\n\npublic_key\x18\x01 \x01(\x0c\x12\x11\n\tsignature\x18\x02 \x01(\x0c\"\x1c\n\nSignedData' \
                   b'\x12\x0e\n\x06\x63rx_id\x18\x01 \x01(\x0c\x42\x02H\x03'

# Add serialized file to descriptor pool
DESCRIPTOR = descriptor_pool.AddSerializedFile(serialized_proto)

# Generate messages and enum descriptors
globals_dict = globals()
protobuf_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals_dict)
protobuf_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'crx3_pb2', globals_dict)

# Adjust serialized options and endpoints if not using C descriptors
if not protobuf_descriptor._USE_C_DESCRIPTORS:
    globals_dict['DESCRIPTOR']._options = None
    globals_dict['DESCRIPTOR']._serialized_options = b'H\003'
    globals_dict['_CRXFILEHEADER']._serialized_start = 25
    globals_dict['_CRXFILEHEADER']._serialized_end = 208
    globals_dict['_ASYMMETRICKEYPROOF']._serialized_start = 210
    globals_dict['_ASYMMETRICKEYPROOF']._serialized_end = 269
    globals_dict['_SIGNEDDATA']._serialized_start = 271
    globals_dict['_SIGNEDDATA']._serialized_end = 299

# @@protoc_insertion_point(module_scope)
