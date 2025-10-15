package com.example;

import javax.swing.JApplet;
import javax.swing.JLabel;
import javax.swing.SwingConstants;
import java.awt.Container;

/**
 * Example Swing applet using deprecated JApplet (removed in JDK 21).
 * This should trigger: jdk-21-applet-api-removal-00005
 */
public class SwingApplet extends JApplet {

    @Override
    public void init() {
        // Get content pane
        Container contentPane = getContentPane();

        // Add a label
        JLabel label = new JLabel("Hello from JApplet!", SwingConstants.CENTER);
        contentPane.add(label);
    }
}
