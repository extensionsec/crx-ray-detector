# CRX-Ray

## Introduction

This tool is used to check whether the AI platform sensitive API Keys exist in the extension files (crx, xpi) of mainstream browsers (Chrome, Edge, Firefox).

## Install

You can download this tool from github through the following git command:

```sh
git clone https://github.com/extensionsec/crx-ray.git
```

Then you should use the `pip install -r requirements.txt` to install the package.

## Usage

Currently this tool supports two extended types of scans：

- crx: Chrome and Edge extension file type
- xpi: Firefox extension file type


```
Usage: python main.py -f <file> [-o <output_file>]

Scan the API Keys of all AI platforms present in the extension file

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -f FILE, --file=FILE  extension file to be scanned
  -o OUTPUT_FILE, --output=OUTPUT_FILE
                        output file to save the scan results
```

Example:

```sh
python main.py -f crx_secret.crx
```

The above command will scan the contents of crx_secret.crx and give the results：

```
$ python main.py -f crx_secret.crx -o a.txt
Searching in crx_secret.crx ...
Found API Keys
  Service Name: OpenAI
  Token: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  Extension Type: crx
  Repository Path: api.js
  Context:
5><p>Loading...</p></div>'

        document.body.appendChild(modal);
        //
        const response = await fetch(
            'https://api.openai.com/v1/chat/completions',
            {
                headers: { 'Authorization': 'Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx','Content-Type': 'application/json'},
                method: 'POST',
                body: JSON.stringify(requestData)
            }
        );
        const result = await response.json();
        console.log(result)
        var returnMsg=r
--------------------------------------------------------------------------------------------------------------------------------------
```

You can also use the following command to store the scan results in a file you specify:

```sh
python main.py -f crx_secret.crx -o result.txt
```

