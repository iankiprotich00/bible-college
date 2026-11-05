# Bible College Portal Prototype: Setup Guide

The whole prototype is one file: `bible-college-portal.html`. It has no install step, no server, and no build tools.

## 1. Run it on your laptop

1. Download `bible-college-portal.html` and put it in a folder, for example `bible-portal`.
2. Double-click the file. It opens in your browser (Chrome, Edge, Firefox, or Safari).
3. Create an account and try it out.

The page loads two fonts from Google Fonts, so you need an internet connection to see them. Without one, it falls back to Georgia and your system font and still works.

## 2. Edit it

Open the file in a code editor. The free **Visual Studio Code** (https://code.visualstudio.com) is a good choice. Notepad also works. Save your changes, then refresh the browser tab to see them.

Optional but handy: in VS Code, install the "Live Server" extension, right-click the file, and choose "Open with Live Server". The page then refreshes by itself every time you save.

## 3. Where to change things

The file has three parts: `<style>` (looks), HTML (page structure), and `<script>` (behavior).

| To change... | Look for... |
|---|---|
| College name | Search for `Cornerstone Bible College` (it appears in the page title, the login screen, and the top bar) |
| Colors | The `:root{--bg ... --accent ...}` block at the top of `<style>`. There is a light set and a dark set |
| Fonts | The Google Fonts `<link>` near the top, and the `font:` lines in `body` and `h1,h2,h3` |
| Login-screen quote | The `<blockquote>` inside `.auth-side` |
| Courses and instructor notes | The `COURSES` list at the start of the `<script>` section |

### Adding a course
Copy one block inside `COURSES` and edit it:

```js
{id:"ch120", code:"CH120", title:"Church History", teacher:"Dr. Jane Doe", notes:[
  {t:"Week 1: The early church", ref:"Acts 8", b:"Your note text here."}
]},
```

Each `id` must be unique, and each course block ends with a comma (except the last).

## 4. Reset your test data

Accounts and notes are saved in your browser's local storage. To wipe them, open the page, press F12, go to the Application (or Storage) tab, choose Local Storage, and delete the entries starting with `bc_`.

## 5. Limits of this prototype

- Accounts and notes live only in the browser on that one laptop, and passwords are stored unprotected.
- Instructors can't log in to add notes. Their notes are typed into the `COURSES` list.
- It is not safe for real student data.

To turn it into a real app, use a backend such as Supabase or Firebase for login and storage, and a hosting service such as Vercel or Netlify. You can bring this file to a developer, or ask me to write a step-by-step build spec for that version.
