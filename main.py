import shutil
import sys
from optparse import OptionParser
from pathlib import Path
from crx_file import CrxFile, BadCrx, BadZipFile
from xpi_file import XpiFile
from configuration import API_PATTERNS

terminal_width = shutil.get_terminal_size().columns


class CommandLineParser:
    """Command line argument parser."""

    def __init__(self):
        self.parser = self.setup_parser()
        self.options, self.args = self.parser.parse_args()

    def setup_parser(self) -> OptionParser:
        """Set up the command line option parser."""
        usage = "python main.py -t <type> -f <file> [-o <output_file>]"
        version = "1.0.0"
        description = "Scan the API Keys of all AI platforms present in the extension file"
        parser = OptionParser(usage=usage, version=version, description=description, add_help_option=True)
        parser.add_option("-t", "--type", type="string", dest="type", help="extension type to be scanned (only supports Crx and Xpi)")
        parser.add_option("-f", "--file", type="string", dest="file", help="extension file to be scanned")
        parser.add_option("-o", "--output", type="string", dest="output_file", help="output file to save the scan results")
        return parser


def search_api_keys_in_extension_file(extension_file_path: Path, extension_type: str, output_file=None):
    """Search API keys in an extension file based on its type."""
    try:
        if extension_type == "crx":
            extension = CrxFile(extension_file_path, filter_list=None)
        elif extension_type == "xpi":
            extension = XpiFile(extension_file_path, filter_list=None)
        else:
            print("Unsupported file type")
            return

        extension.setup()
    except (BadCrx, BadZipFile) as error:
        print(f"Could not read {extension_type} {extension_file_path}. {error}")
        return

    print(f"Searching in {extension_file_path} ...")

    with sys.stdout as terminal_output:
        for resource in extension.resources:
            if resource.content is None:
                continue

            try:
                content_bytes = resource.content.read()
                content_string = content_bytes.decode("utf-8", errors="replace")
            except UnicodeDecodeError:
                print(f"Decode error in {extension.digest} for {resource.repository_path}")
                continue

            for api_pattern in API_PATTERNS:
                matches = api_pattern.find_matches_with_context(content_string)

                for service_name, token, context in matches:
                    
                    # NOTE: removed the unknown service pattern
                    if service_name is "Unknown":
                        continue

                    # Highlight token in context
                    highlighted_context = context.replace(token, f"\033[91m{token}\033[0m")

                    # Print to terminal
                    terminal_output.write(f"\033[94mFound API Keys\033[0m\n")
                    terminal_output.write(f"  \033[92mService Name:\033[0m {service_name}\n")
                    terminal_output.write(f"  \033[93mToken:\033[0m {token}\n")
                    terminal_output.write(f"  \033[91mExtension Type:\033[0m {extension_type}\n")
                    terminal_output.write(f"  \033[95mRepository Path:\033[0m {resource.repository_path}\n")
                    terminal_output.write(f"  \033[96mContext:\033[0m\n{highlighted_context}\n")
                    terminal_output.write("-" * terminal_width + "\n")  # Dynamic separator based on terminal width

                    # Write to output file if specified
                    if output_file:
                        with open(output_file, "a") as file_output:
                            file_output.write(f"Found API Keys\n")
                            file_output.write(f"  Service Name: {service_name}\n")
                            file_output.write(f"  Token: {token}\n")
                            file_output.write(f"  Extension Type: {extension_type}\n")
                            file_output.write(f"  Repository Path: {resource.repository_path}\n")
                            file_output.write(f"  Context:\n{context}\n")
                            file_output.write("-" * terminal_width + "\n")


def main():
    """Main function to handle the scanning process."""
    parser = CommandLineParser()
    extension_type = parser.options.type
    file_path = parser.options.file
    output_file = parser.options.output_file

    if not file_path:
        print("Please provide a file path.")
        exit(0)

    if extension_type not in ["crx", "xpi"]:
        print("Invalid extension type. Only 'crx' and 'xpi' are supported.")
        exit(0)

    search_api_keys_in_extension_file(Path(file_path), extension_type, output_file)


if __name__ == "__main__":
    main()
