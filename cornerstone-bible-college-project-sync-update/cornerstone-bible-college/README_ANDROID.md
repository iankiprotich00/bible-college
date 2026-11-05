# Cornerstone Portal: Android test app

This folder contains an Android Studio project (`android-app`) that turns the portal into an installable Android
app, plus a download page on the Python server so phones on your Wi-Fi can install it.

The app is a thin shell: it shows the portal web page from your Python server full screen, remembers the server
address, and lets students attach files to assignments. Everything else (logins, the database) is the same as in
the browser.

IMPORTANT: the `.apk` file itself is not included. It has to be compiled with the Android build tools, which weren't
available where this project was written. The project is complete and its Java code was checked for errors, but it has
not been built or run on a phone yet. Expect to fix small things on the first build.

## 1. Build the test APK (about 15 minutes the first time)
1. Install **Android Studio** (free): https://developer.android.com/studio
2. Choose **File > Open** and select the `android-app` folder. Wait for "Gradle sync" to finish. The first time it
   downloads Gradle and the Android SDK, so you need internet. Accept any "install SDK / platform 34" prompts.
3. Choose **Build > Build Bundle(s) / APK(s) > Build APK(s)**. When it finishes, click **locate**.
   The file is `app/build/outputs/apk/debug/app-debug.apk`.
4. Copy it into the `downloads` folder (next to `server.py`) and rename it `cornerstone-test.apk`.

Command-line alternative (needs JDK 17 or 21, the Android SDK with `ANDROID_HOME` set, and Gradle 8.7 or newer):
`cd android-app && gradle assembleDebug`

## 2. Start the server so phones can reach it
```
python3 server.py --host 0.0.0.0
```
(On Windows: `py server.py --host 0.0.0.0`. If Windows Firewall asks, allow Python on **private** networks.)
It prints two addresses, for example:
```
On your phone (same Wi-Fi): http://192.168.1.20:8000
Test app download page:      http://192.168.1.20:8000/download
```

## 3. Install on a phone
1. Connect the phone to the **same Wi-Fi** as the computer.
2. In the phone's browser, open the **download page** address.
3. Tap the download button, open the file, and allow **install unknown apps** if asked.
   (Android may also warn the app isn't from the Play Store. That's expected for a test build.)
4. Open **Cornerstone Portal (test)**. When it asks for the server address, enter the first address above
   (for example `http://192.168.1.20:8000`).
5. Sign up or log in. Logins are checked by the server and recorded in `portal.db`.

On the Android emulator, use `http://10.0.2.2:8000` as the server address.

## Good to know
- **The download link only works on your own Wi-Fi.** It is not a public link. Sharing it with people elsewhere
  needs real hosting (see the earlier hosting steps).
- **Changing the server address:** if the app can't connect, it offers "Change address". You can also clear the
  app's data in Android settings.
- **Updating the app:** build again and reinstall. Installing over the old version works if it was built on the same
  computer. Otherwise uninstall the old one first.
- **Test build only.** It is signed with a debug key and allows plain `http` traffic (see
  `app/src/main/res/xml/network_security_config.xml`). A real release needs https, a proper signing key, and the
  Play Store steps.
- Only logins use the database so far. Notes, enrolments, assignments, fees and marks are still saved inside the app
  on each phone. File attachments save only the file name.
- The phone must be able to reach the computer. Public or "guest" Wi-Fi networks often block this.

## If the first build fails
- "SDK location not found": in Android Studio open **File > Settings > Languages & Frameworks > Android SDK** and
  install Android 14 (API 34).
- Gradle or Android Gradle Plugin version warnings: accept Android Studio's offer to update them (the project is set up for Gradle 8.7 and Android Gradle Plugin 8.3.2, which work with current Android Studio).
- Still stuck: copy the error text and ask for help, and it can be fixed quickly.
