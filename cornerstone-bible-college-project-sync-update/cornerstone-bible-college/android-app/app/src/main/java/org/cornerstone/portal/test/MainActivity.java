package org.cornerstone.portal.test;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.ViewGroup;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;

/**
 * Test shell for the Cornerstone Bible College portal.
 * It shows the portal web page served by the Python server (server.py) full screen,
 * remembers the server address, and supports file attachments for assignments.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "portal";
    private static final String KEY_URL = "server_url";
    private static final int FILE_CHOOSER = 1;

    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private boolean dialogOpen = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String base = serverUrl();
                if (base != null && request.getUrl().toString().startsWith(base)) {
                    return false;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, request.getUrl()));
                } catch (Exception ignored) {
                    // no app can open this link
                }
                return true;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showError();
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (fileCallback != null) {
                    fileCallback.onReceiveValue(null);
                }
                fileCallback = callback;
                try {
                    startActivityForResult(params.createIntent(), FILE_CHOOSER);
                } catch (Exception e) {
                    fileCallback = null;
                    return false;
                }
                return true;
            }
        });

        load();
    }

    private String serverUrl() {
        return getSharedPreferences(PREFS, MODE_PRIVATE).getString(KEY_URL, null);
    }

    private static String normalize(String raw) {
        String u = raw == null ? "" : raw.trim();
        if (u.isEmpty() || u.equals("http://") || u.equals("https://")) {
            return null;
        }
        if (!u.startsWith("http://") && !u.startsWith("https://")) {
            u = "http://" + u;
        }
        while (u.endsWith("/")) {
            u = u.substring(0, u.length() - 1);
        }
        return u;
    }

    private void load() {
        String base = serverUrl();
        if (base == null) {
            askServer();
        } else {
            web.loadUrl(base + "/");
        }
    }

    private void askServer() {
        if (dialogOpen) {
            return;
        }
        dialogOpen = true;
        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        input.setHint("http://192.168.1.20:8000");
        String current = serverUrl();
        input.setText(current != null ? current : "http://");

        new AlertDialog.Builder(this)
                .setTitle("College server address")
                .setMessage("Enter the address shown on the server's download page.")
                .setView(input)
                .setCancelable(current != null)
                .setPositiveButton("Connect", (dialog, which) -> {
                    dialogOpen = false;
                    String url = normalize(input.getText().toString());
                    if (url == null) {
                        askServer();
                        return;
                    }
                    getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(KEY_URL, url).apply();
                    web.loadUrl(url + "/");
                })
                .setOnCancelListener(dialog -> dialogOpen = false)
                .show();
    }

    private void showError() {
        if (dialogOpen) {
            return;
        }
        dialogOpen = true;
        new AlertDialog.Builder(this)
                .setTitle("Can\u2019t reach the server")
                .setMessage("Check that the server is running, that your phone is on the same Wi-Fi, "
                        + "and that the address is right:\n" + serverUrl())
                .setPositiveButton("Try again", (dialog, which) -> {
                    dialogOpen = false;
                    load();
                })
                .setNegativeButton("Change address", (dialog, which) -> {
                    dialogOpen = false;
                    askServer();
                })
                .setOnCancelListener(dialog -> dialogOpen = false)
                .show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER) {
            if (fileCallback != null) {
                fileCallback.onReceiveValue(
                        WebChromeClient.FileChooserParams.parseResult(resultCode, data));
                fileCallback = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.destroy();
        }
        super.onDestroy();
    }
}
