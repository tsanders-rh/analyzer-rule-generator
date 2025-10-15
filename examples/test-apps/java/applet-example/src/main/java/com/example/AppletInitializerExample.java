package com.example;

import java.applet.Applet;
import java.beans.AppletInitializer;

/**
 * Example using AppletInitializer interface (removed in JDK 21).
 * This should trigger:
 *  - jdk-21-applet-api-removal-00001 (Applet)
 *  - jdk-21-applet-api-removal-00006 (AppletInitializer)
 */
public class AppletInitializerExample implements AppletInitializer {

    @Override
    public void initialize(Applet newAppletBean, java.beans.beancontext.BeanContext bCtxt) {
        // Initialize the applet
        System.out.println("Initializing applet: " + newAppletBean.getName());
    }

    @Override
    public void activate(Applet newApplet) {
        System.out.println("Activating applet");
    }
}
