# Logo Setup Instructions

## Logo File Placement

Place your logo file in this directory (`frontend/public/`) with the name `logo.png`.

## Supported Formats

The logo component supports:
- **PNG** (recommended for logos with transparency)
- **SVG** (best for scalability, but requires code changes)
- **JPG/JPEG** (if no transparency needed)

## Current Implementation

The logo is currently configured to load from `/logo.png`. 

### To use PNG:
1. Place your logo file as `logo.png` in the `frontend/public/` folder
2. The component will automatically load it

### To use SVG:
1. Place your logo file as `logo.svg` in the `frontend/public/` folder
2. Update `frontend/components/ui/logo.tsx`:
   - Change `src="/logo.png"` to `src="/logo.svg"`

### Recommended Logo Specifications:
- **Size**: 512x512px or larger (for high DPI displays)
- **Format**: PNG with transparency
- **Aspect Ratio**: Square (1:1) works best
- **Background**: Transparent preferred

## Fallback

If the logo file is not found, the component will automatically show a fallback:
- A circular badge with the letter "F" (for Fairly)
- The app name "Fairly" next to it (if `showText={true}`)

## Usage

The logo is used in:
- `ChatHeader` component (header bar)
- Can be used anywhere by importing: `import Logo from '@/components/ui/logo'`

Example:
```tsx
<Logo width={32} height={32} showText={true} />
```

