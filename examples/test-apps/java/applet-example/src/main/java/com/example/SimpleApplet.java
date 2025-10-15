package com.example;

import java.applet.Applet;
import java.applet.AudioClip;
import java.awt.Graphics;

/**
 * Example applet using deprecated Applet API (removed in JDK 21).
 * This should trigger: jdk-21-applet-api-removal-00001
 */
public class SimpleApplet extends Applet {

    private AudioClip sound;

    @Override
    public void init() {
        // Initialize the applet
        System.out.println("Applet initialized");

        // Load an audio clip (uses deprecated AudioClip interface)
        // This should trigger: jdk-21-applet-api-removal-00004
        sound = getAudioClip(getCodeBase(), "sounds/hello.wav");
    }

    @Override
    public void paint(Graphics g) {
        g.drawString("Hello from Applet!", 50, 50);
    }

    @Override
    public void start() {
        if (sound != null) {
            sound.play();
        }
    }

    @Override
    public void stop() {
        if (sound != null) {
            sound.stop();
        }
    }
}
