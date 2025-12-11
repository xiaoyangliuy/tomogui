Themes
======

TomoGUI supports bright and dark color themes for improved visibility and reduced eye strain during long working sessions.

Theme Toggle
------------

Switch between themes using the theme toggle button in the toolbar:

- **🌙 Moon icon**: Currently in bright mode, click to switch to dark
- **☀ Sun icon**: Currently in dark mode, click to switch to bright

The theme button is located in the right panel toolbar, next to the Min/Max contrast controls.

Available Themes
----------------

Bright Theme
~~~~~~~~~~~~

The bright theme features:

- Light gray background (#f5f5f5)
- Dark text (#212121)
- Clean, professional appearance
- Reduced glare in well-lit environments
- Default theme on first launch

**Best for:**
   - Well-lit laboratories
   - Daytime use
   - Users who prefer traditional interfaces

Dark Theme
~~~~~~~~~~

The dark theme features:

- Dark background (#2b2b2b)
- Light text (#e0e0e0)
- Reduced eye strain
- Better contrast in dim lighting
- Modern aesthetic

**Best for:**
   - Low-light environments
   - Extended work sessions
   - Reducing eye fatigue
   - Night work

Theme Components
----------------

Both themes style the entire interface consistently:

User Interface
~~~~~~~~~~~~~~

- **Buttons**: Matching background and border colors
- **Text fields**: Contrasting input areas
- **Dropdowns**: Consistent styling with hover effects
- **Tables**: Alternating row colors (in batch tab)
- **Tabs**: Active/inactive states
- **Progress bars**: Visible progress indication
- **Scrollbars**: Subtle but usable

Matplotlib Plots
~~~~~~~~~~~~~~~~

Both themes include matching matplotlib styles:

Bright Theme:
   - White figure background
   - Light gray axes
   - Dark axis labels and text
   - Light grid lines

Dark Theme:
   - Dark gray figure background
   - Slightly lighter axes area
   - Light axis labels and text
   - Subtle grid lines

Theme Persistence
-----------------

Theme preference is automatically saved and restored:

**Saved to**: ``~/.tomogui_settings.json``

**Format**:

.. code-block:: json

   {
     "theme": "dark"
   }

The selected theme persists across sessions. When you restart TomoGUI, your last-used theme is automatically applied.

Customization
-------------

For developers wanting to customize themes:

Theme Files
~~~~~~~~~~~

**Qt Stylesheets**:
   - ``src/tomogui/styles/themes.py``
   - Contains QSS definitions for both themes

**Matplotlib Styles**:
   - ``src/tomogui/styles/tomoGUI_mpl_bright.mplstyle``
   - ``src/tomogui/styles/tomoGUI_mpl_dark.mplstyle``

Theme Manager
~~~~~~~~~~~~~

The theme system is managed by:
   - ``src/tomogui/theme_manager.py``
   - Handles theme switching
   - Applies Qt and matplotlib styles
   - Manages persistence

Modifying Themes
~~~~~~~~~~~~~~~~

To modify colors:

1. Edit ``src/tomogui/styles/themes.py``
2. Update color values in BRIGHT_THEME or DARK_THEME
3. Restart TomoGUI to see changes

Example color modification:

.. code-block:: python

   # In themes.py
   DARK_THEME = """
   QWidget {
       background-color: #1a1a1a;  # Even darker background
       color: #f0f0f0;              # Brighter text
   }
   """

Keyboard Shortcuts
------------------

Currently, theme switching is available via mouse click only.

For power users who want a keyboard shortcut, this feature can be added to future versions.

Accessibility
-------------

Theme Contrast
~~~~~~~~~~~~~~

Both themes are designed with WCAG contrast guidelines in mind:

- Text-to-background ratios exceed 4.5:1
- Interactive elements are clearly distinguishable
- Focus indicators are visible

Color Blindness
~~~~~~~~~~~~~~~

Status indicators use both color and symbols:

- ✅ Success (green + checkmark)
- ❌ Failure (red + X)
- ⚠️ Warning (orange + warning triangle)
- 🚀 Start (blue + rocket)

This ensures information is conveyed through multiple channels.

Tips and Tricks
---------------

Optimal Viewing
~~~~~~~~~~~~~~~

**For Bright Theme:**
   - Adjust room lighting to avoid screen glare
   - Consider reducing screen brightness slightly
   - Use in well-lit environments

**For Dark Theme:**
   - Reduce ambient lighting for best contrast
   - Increase screen brightness if text is hard to read
   - Give eyes time to adjust (30 seconds)

Switching Frequency
~~~~~~~~~~~~~~~~~~~

It's safe to switch themes as often as needed:

- Changes apply instantly
- No data is lost
- Matplotlib plots update automatically
- Previous theme state is saved

Performance
~~~~~~~~~~~

Theme switching is lightweight:

- Instant visual update
- No processing delay
- Minimal memory usage
- No effect on running reconstructions

Troubleshooting
---------------

Theme Not Changing
~~~~~~~~~~~~~~~~~~

If the theme doesn't change when clicked:

1. Check that button icon updates (🌙 ↔ ☀)
2. Restart TomoGUI
3. Delete ``~/.tomogui_settings.json`` and try again
4. Check console for error messages

Matplotlib Plots Not Updating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If plots don't match the theme:

1. Close and reopen any visualization windows
2. Click "View Try" or "View Full" again
3. Restart TomoGUI

Theme Persistence Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If theme doesn't persist between sessions:

1. Check write permissions on home directory
2. Verify ``~/.tomogui_settings.json`` exists
3. Check file contents match expected format
4. Look for errors in console output

Future Enhancements
-------------------

Potential future theme features:

- Custom color pickers
- Multiple theme presets
- High contrast mode
- Theme import/export
- Per-panel theme control

These features may be added based on user feedback.
