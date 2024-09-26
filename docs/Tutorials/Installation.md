# Installation Guide for Kryptonite

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1. **Python**: Kryptonite requires Python 3.6 or higher. You can download Python from the [official website](https://www.python.org/downloads/).

2. **pip**: This is the package installer for Python. It is usually included with Python, but you can verify its installation by running:
    ```sh
    pip --version
    ```
    If you don't have pip installed, you can follow the instructions [here](https://pip.pypa.io/en/stable/installation/).
3. **ffmpeg**: This is a multimedia framework that can decode, encode, transcode, mux, demux, stream, filter, and play almost anything that humans and machines have created. You can download ffmpeg from the [official website](https://www.ffmpeg.org/download.html).
4. **bento4**: This is a set of tools to read and write QuickTime files. You can download bento4 from the [official website](https://www.bento4.com/downloads/).

## Installation Steps

1. **Clone the repository**:
    ```sh
    git clone https://github.com/JacobCrume/Kryptonite.git
    ```
2. **Enter the repository directory**:
    ```sh
    cd Kryptonite
   ```
3. **Install the required packages**:
    ```sh
    pip install -r requirements.txt
    ```
4. **Install the CDM module**:
    - Obtain your own Widevine L3 CDM module, namely the "client_id.bin" and "private_key.pem" files.
    - Copy both of those files into the `Kryptonite/cdm/devices/android_generic` directory.
    - Your directory should look like this:
        ```
        android_generic/
        ├── client_id.bin
        ├── config.json
        ├── private_key.pem
        └── token.bin
        ```

## Conclusion

And that's it! With a little luck, you should now have Kryptonite installed on your system.

**Next steps:**
- [Getting Started with Kryptonite](../Tutorials/Getting-Started.md)
- [API Reference](../Reference/TVNZ.md)
- [How Kryptonite Works](../Explanations/Downloading.md) 
   