# Turning the portal into an Android app

The folder is a PWA (installable web app). Two routes from here.

## Route A: Install straight from the browser (no APK, 5 minutes)
1. Upload this whole folder to any free HTTPS host:
   - Netlify Drop: go to https://app.netlify.com/drop and drag the folder onto the page, or
   - GitHub Pages, Cloudflare Pages, or Vercel.
2. Open the site's link in Chrome on an Android phone.
3. Tap the menu (three dots), then "Install app" (or "Add to Home screen").
It gets its own icon, opens full-screen, and works offline after the first visit.

## Route B: Get a real .apk file to share or sideload
After step 1 above (you need the live HTTPS link):
1. Go to https://www.pwabuilder.com and paste your site's link.
2. Choose "Package for stores", then Android.
3. Download the package. It contains an .apk (for sideloading) and an .aab (for Google Play).
4. Send the .apk to a phone and open it. Android will ask you to allow installs from that source.
For Google Play you need a developer account (one-time US$25 fee) and the .aab file.

## Route C: Build it yourself with Capacitor (full control, needs Android Studio)
1. Install Node.js (https://nodejs.org) and Android Studio (https://developer.android.com/studio).
2. In a terminal, in a new empty folder:
   npm init -y
   npm i @capacitor/core @capacitor/cli @capacitor/android
   npx cap init "Cornerstone" org.yourcollege.portal --web-dir=www
3. Create a folder named www and copy every file from this folder into it.
4. Run:
   npx cap add android
   npx cap sync
   npx cap open android
5. In Android Studio choose Build > Build Bundle(s) / APK(s) > Build APK(s).
The debug .apk appears under android/app/build/outputs/apk/debug/.

## Important
This is still the prototype: accounts and notes are stored on each phone only, with no password protection. Each student would see only their own device's data. Before real students use it, it needs a backend (Supabase or Firebase) for login and storage.
