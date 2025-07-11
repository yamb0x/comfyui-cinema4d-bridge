# UI Design System - ComfyUI to Cinema4D Bridge

## 🎨 Design Philosophy
Simple, clean, dark-themed interface optimized for creative workflows. Focus on functionality over decoration.

## 🎯 Core Principles
1. **Consistency** - Same patterns across all screens
2. **Clarity** - Clear visual hierarchy
3. **Efficiency** - Minimal clicks to achieve tasks
4. **Familiarity** - Follow Cinema4D and professional app conventions

## 🌑 Color Palette

### Primary Colors
```css
--background-primary: #1a1a1a    /* Main app background */
--background-secondary: #2b2b2b  /* Panel backgrounds */
--background-tertiary: #333333   /* Input backgrounds */
--border-color: #444444          /* Borders and dividers */
```

### Text Colors
```css
--text-primary: #ffffff          /* Main text */
--text-secondary: #cccccc        /* Secondary text */
--text-disabled: #666666         /* Disabled text */
--text-accent: #4a9eff          /* Links and highlights */
```

### Status Colors
```css
--status-success: #4caf50        /* Success, connected */
--status-warning: #ff9800        /* Warnings */
--status-error: #f44336          /* Errors */
--status-info: #2196f3           /* Information */
```

### Button Colors
```css
--button-primary: #4a9eff        /* Primary actions */
--button-secondary: #444444      /* Secondary actions */
--button-danger: #f44336         /* Destructive actions */
--button-hover: #5aafff          /* Hover state */
```

## 📏 Typography

### Font Stack
```css
font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
```

### Font Sizes
```css
--font-size-xs: 11px    /* Small labels */
--font-size-sm: 12px    /* Secondary text */
--font-size-base: 13px  /* Body text */
--font-size-lg: 14px    /* Headings */
--font-size-xl: 16px    /* Page titles */
```

### Font Weights
```css
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-bold: 600
```

## 📐 Spacing System (8px Grid)

### Base Unit
All spacing based on 8px grid for consistency:

```css
--space-xs: 4px     /* Tight spacing */
--space-sm: 8px     /* Small spacing */
--space-md: 16px    /* Medium spacing */
--space-lg: 24px    /* Large spacing */
--space-xl: 32px    /* Extra large */
--space-xxl: 48px   /* Section spacing */
```

### Component Spacing
- **Button padding**: 8px 16px
- **Input padding**: 8px 12px
- **Panel padding**: 16px
- **Section margins**: 24px
- **Dialog padding**: 24px

## 🧩 Component Patterns

### Buttons

#### Primary Button
```css
.button-primary {
    background: var(--button-primary);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
}

.button-primary:hover {
    background: var(--button-hover);
}
```

#### Compact Button (Scene Assembly)
```css
.button-compact {
    height: 24px;
    padding: 4px 12px;
    font-size: var(--font-size-xs);
}
```

#### Icon Button
```css
.button-icon {
    width: 24px;
    height: 24px;
    padding: 4px;
    border-radius: 4px;
}
```

### Input Fields

#### Text Input
```css
.input-text {
    background: var(--background-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 8px 12px;
    color: var(--text-primary);
    font-size: var(--font-size-base);
}

.input-text:focus {
    border-color: var(--button-primary);
    outline: none;
}
```

#### Number Input
- Include unit suffix (cm, °, %)
- Right-aligned text
- Spinner buttons on hover only

### Panels

#### Standard Panel
```css
.panel {
    background: var(--background-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
```

#### Collapsible Section
- Header with chevron icon
- Smooth expand/collapse animation
- Nested content indented by 16px

### Dialogs

#### Modal Dialog
```css
.dialog {
    background: var(--background-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}
```

#### Dialog Layout
- Title at top (16px font)
- Content area with scrollbar if needed
- Button bar at bottom (right-aligned)
- Standard buttons: Cancel, Apply, OK

### Tabs

#### Tab Navigation
```css
.tab-header {
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 16px;
}

.tab-button {
    padding: 8px 16px;
    border-bottom: 2px solid transparent;
}

.tab-button.active {
    border-bottom-color: var(--button-primary);
    color: var(--text-primary);
}
```

## 📱 Layout Patterns

### Main Window Structure
```
┌─────────────────────────────────────┐
│ Menu Bar                            │
├─────────────────────────────────────┤
│ Tab Bar                             │
├─────────────────────────────────────┤
│                                     │
│ Content Area                        │
│                                     │
├─────────────────────────────────────┤
│ Status Bar                          │
└─────────────────────────────────────┘
```

### Tab Content Layout
```
┌─────────────────────────────────────┐
│ Section Title                       │
├─────────────────────────────────────┤
│ ┌─────────┐ ┌─────────────────────┐ │
│ │ Sidebar │ │ Main Content        │ │
│ │         │ │                     │ │
│ │ Controls│ │ Preview/Results     │ │
│ │         │ │                     │ │
│ └─────────┘ └─────────────────────┘ │
└─────────────────────────────────────┘
```

### Form Layout
- Labels above inputs
- Group related fields
- Required fields marked with *
- Help text below inputs (smaller, dimmed)

## 🎯 Interaction Patterns

### Hover States
- Buttons: Lighten by 10%
- Inputs: Show border highlight
- List items: Show background highlight

### Focus States
- Blue border (2px)
- No outline
- Tab navigation support

### Loading States
- Spinner for async operations
- Progress bar for long operations
- Disable UI during operation
- Show status in status bar

### Error Handling
- Red border on invalid inputs
- Error message below field
- Toast notifications for system errors
- Non-blocking whenever possible

## 📊 Specific Component Guidelines

### Scene Assembly View
- Compact buttons (24px height)
- Grid layout for objects
- Visual command buttons with icons
- Settings wheel (⚙️) for configuration
- X button (✗) for removal
- NL trigger inputs with debouncing

### 3D Viewer
- Dark background (#1a1a1a)
- Subtle grid with low opacity
- Orbit controls in corner
- Model info overlay
- Thumbnail grid for multiple models

### Workflow Parameters
- Collapsible sections
- Smart defaults
- Live validation
- Preview on change

## 🚀 Implementation Notes

### Qt/PySide6 Specifics
```python
# Set dark theme
app.setStyle("Fusion")
palette = QPalette()
palette.setColor(QPalette.Window, QColor(26, 26, 26))
palette.setColor(QPalette.WindowText, Qt.white)
app.setPalette(palette)
```

### Custom Widgets
- Extend Qt widgets for consistency
- Create reusable components
- Document custom properties

### Responsive Design
- Minimum window size: 1200x800
- Flexible layouts using QSplitter
- Collapsible panels for small screens

## 📋 Checklist for New Screens

- [ ] Uses standard color palette
- [ ] Follows 8px grid spacing
- [ ] Consistent typography
- [ ] Standard button styles
- [ ] Proper hover/focus states
- [ ] Loading indicators
- [ ] Error handling
- [ ] Keyboard navigation
- [ ] Status bar updates
- [ ] Follows layout patterns

## 🎨 Visual Examples

### Button States
```
Normal:  [█████████]
Hover:   [░░░░░░░░░]
Active:  [▓▓▓▓▓▓▓▓▓]
Disabled:[┅┅┅┅┅┅┅┅┅]
```

### Panel Hierarchy
```
Level 1: ████████████████
Level 2: ░░░░████████░░░░
Level 3: ░░░░░░████░░░░░░
```

This design system ensures consistency across all current and future screens while maintaining a professional, Cinema4D-compatible appearance.