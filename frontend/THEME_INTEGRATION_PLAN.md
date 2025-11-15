# Caffeine Theme Integration Plan

## Overview
This document outlines the plan to integrate the Caffeine theme from tweakcn.com into the Fairly frontend application.

## Theme Source
- **Theme Name**: Caffeine
- **Source**: tweakcn.com
- **Color Format**: OKLCH (Modern color space for better color consistency)
- **File**: `frontend/trial-theme.md`

## Implementation Strategy

### Phase 1: Color System Migration
**Current State:**
- Using HSL color format in CSS variables
- Basic color variables only
- No sidebar-specific colors

**Target State:**
- Migrate to OKLCH color format
- Include all Caffeine theme variables
- Add sidebar-specific color variables
- Support both light and dark modes

### Phase 2: Tailwind Configuration
**Changes Required:**
- Update Tailwind config to use OKLCH instead of HSL
- Ensure color variables are properly referenced
- Add sidebar color tokens if needed

### Phase 3: Component Updates
**Components to Review:**
- Sidebar components (use sidebar color variables)
- Cards and containers
- Inputs and forms
- Buttons and interactive elements
- Borders and shadows

### Phase 4: Testing
- Verify dark mode works correctly
- Check all components render properly
- Ensure no functionality is broken
- Test color contrast and accessibility

## Key Features of Caffeine Theme

### Color Palette
- **Primary**: Yellow/gold accent (oklch(0.9247 0.0524 66.1732) in dark mode)
- **Background**: Dark, rich backgrounds
- **Cards**: Slightly lighter than background
- **Borders**: Subtle, well-defined borders
- **Sidebar**: Dedicated sidebar color scheme

### Design Characteristics
- Modern OKLCH color space
- Professional dark theme
- Warm yellow/gold accents
- Excellent contrast ratios
- Sidebar-specific styling

## Implementation Steps

1. ✅ Replace HSL variables with OKLCH in globals.css
2. ✅ Update Tailwind config color references
3. ✅ Add sidebar color variables
4. ✅ Update sidebar components to use sidebar colors
5. ✅ Test all components

## Notes
- OKLCH is natively supported in modern browsers
- Tailwind CSS v3.3+ supports OKLCH
- All functionality must remain unchanged
- Only visual styling will be modified

