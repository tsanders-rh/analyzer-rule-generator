package com.example;

import java.applet.Applet;
import java.applet.AppletContext;
import java.net.URL;

/**
 * Example using AppletContext interface (removed in JDK 21).
 * This should trigger:
 *  - jdk-21-applet-api-removal-00001 (Applet)
 *  - jdk-21-applet-api-removal-00002 (AppletContext)
 */
public class AppletContextExample extends Applet {

    @Override
    public void init() {
        // Get the applet context
        AppletContext context = getAppletContext();

        if (context != null) {
            try {
                URL docUrl = new URL("http://example.com/docs");
                context.showDocument(docUrl);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
