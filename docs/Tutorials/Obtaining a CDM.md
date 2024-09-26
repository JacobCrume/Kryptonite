# Obtaining a CDM

In order for Kryptonite to download and decrypt Widevine DRM protected content (which almost every streaming service uses), you must obtain a valid Widevine L3 Content Decryption Module (CDM). This is a key requirement for Kryptonite to work, and without it, you will not be able to download any content.

The process of obtaining a CDM is not straightforward, and it involves some reverse engineering and a bit of luck. The general process involves extracting the CDM from an emulated Android device, and then installing it so that Kryptonite can access it. 

## What is a CDM?

In short, a CDM (Content Decryption Module) is a piece of software that decrypts Widevine DRM protected content. Widevine classifies CDMs into three levels: L1, L2, and L3. L1 is the most secure, and is used in hardware-based DRM systems. L2 is software-based, and L3 is the least secure, and is used in most streaming services. Kryptonite only supports L3 CDMs, as they are the most common.

## Getting Your Hands on a CDM

There are a few ways to obtain a CDM, but the most common method is to extract it from an emulated Android device. This process involves setting up an Android emulator, installing a few apps to monitor the emulator's network, and then extracting the CDM from the emulator.

### Setting Up an Android Emulator

The first step is to establish the necessary environment to run the emulator. First up, you'll need to install Android Studio, which is the official IDE for Android development. You can download it [here](https://developer.android.com/studio).

After installing Android Studio, you'll need to set up an Android Virtual Device (AVD) to run the emulator. You can do this by first launching Android Studio and creating a new project. It doesn't matter what this is called, as this we just need to use the emulator. When it asks you to choose a template, just pick the blank one.

To set up the emulator, head to `Tools > Device Manager` and click the `+` button to create a new virtual device. You can choose any device you like, but I recommend using a **Pixel 7 Pro with API Level 28**, as this is a know working configuration. The next step involves choosing an image to run on the emulator.

To avoid running into issues later, make sure that you pick an image that has the Google APIs installed, but **not the play store**. I'd highly recommend choosing `Android 9 (Google APIs)` as this is again a known working configuration, but feel free to experiment with this. Depending on your version of Android Studio, you may have to look for this in the `Other Images` tab.

Once your device is all set up, feel free to fire it up and make sure that it's working. You can check this by running the following command in your terminal:

```bash
adb devices
```

If you see your device listed, you're good to go! If not, you might want to double-check that you have android-tools installed on your system. This is usually installed as part of Android Studio, but you can also install it separately from [Google's website](https://developer.android.com/studio). 

### Installing Monitoring Apps

The next step is to install a few apps on the emulator to monitor its network traffic. Specifically, we are going to be using Frida Server, which is a dynamic instrumentation toolkit used for reverse engineering. You can install it directly from their GitHub page using the following commands:

```bash
wget https://github.com/frida/frida/releases/download/16.0.8/frida-server-16.0.8-android-x86_64.xz
unxz frida-server-16.0.8-android-x86_64.xz 
```

Having downloaded and unzipped the release, you'll need to push the file to your emulated android device:
    
```bash
 adb push frida-server-16.0.8-android-x86_64 /sdcard/
```

Finally, you'll need to open a shell on the device and run the server:

```bash
adb push frida-server-16.0.8-android-x86_64 /sdcard
adb shell
su
mv /sdcard/frida-server-16.0.8-android-x86_64 /data/local/tmp
chmod  +x /data/local/tmp/frida-server-16.0.8-android-x86_64
/data/local/tmp/frida-server-16.0.8-android-x86_64
```

### Extracting the CDM

Now that we have Frida running, we can start monitoring the network traffic on the emulator. To do this, we need to fire up another terminal (make sure to keep the other one open and running) on our computer and create a dedicated project directory. Within this directory, we'll set up a python virtual environment and install the necessary packages:

```bash
using python -m venv ./.
pip install frida==16.0.8 frida-tools==12.0.4 protobuf==3.19.0 pycryptodome
```
It's important that we use these specific versions of the packages and if you want to use a later version of Frida Server, you may have to do some additional work to get it to work with the python packages.

Now that we have the environment set up, we'll clone the Widevine L3 Decryptor repository and run the script to extract the CDM:

```bash
git clone https://github.com/wvdumper/dumper l3keydump
cd l3keydump
python dump_keys.py
```
Back on the emulated device, open any website that uses Widevine DRM on Chrome and start playing some content. https://bitmovin.com/demos/drm. works quite well for this purpose.

If everything is set up correctly, you should see some output in the terminal where you ran the `python dump_keys.py` command, followed by a new `./key_dumps` directory being created in your project directory. This directory contains the extracted CDM files, which you can now use with Kryptonite.

### Installing the CDM

After extracting the CDM, you'll need to place the files in the `Kryptonite/cdm/devices/android_generic` directory. This is the default location that Kryptonite looks for CDM files, so it's important that you place them here with the `client_id.bin` and `private_key.pem` names.

After placing your CDM files here, your directory should look something like this:

```
android_generic/
├── client_id.bin
├── config.json
├── private_key.pem
└── token.bin
```

## Conclusion

And that's it! You should now have a working CDM that you can use with Kryptonite to download and decrypt Widevine DRM protected content. Next up, perhaps try writing your first script to download some content from TVNZ using one of the tutorials!