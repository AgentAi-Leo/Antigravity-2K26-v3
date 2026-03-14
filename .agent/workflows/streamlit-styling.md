---
description: How to style specific Streamlit components - NEVER use CSS wrapper divs
---

# Streamlit Styling Rules

## ❌ NEVER DO THIS (It DOES NOT work)
```python
# This creates SIBLING elements, NOT parent-child nesting!
st.markdown("<div class='my-wrapper'>", unsafe_allow_html=True)
st.expander("My Expander")  # This is NOT inside the div!
st.markdown("</div>", unsafe_allow_html=True)

# Therefore these CSS selectors will NEVER match:
# .my-wrapper svg { display: none; }
# .my-wrapper [data-testid="stExpander"] { ... }
```

**WHY:** Streamlit renders each `st.*` call as an independent sibling DOM element. `st.markdown` divs cannot wrap other Streamlit components.

## ✅ ALWAYS DO THIS INSTEAD

Use **JavaScript via `components.html()`** to find and style elements post-render:

```python
components.html("""
<script>
(function styleMyComponent() {
    // Find element by text content, data-testid, or position
    const allSummaries = window.parent.document.querySelectorAll('div[data-testid="stExpander"] summary');
    let target = null;
    for (const s of allSummaries) {
        if (s.textContent && s.textContent.includes('MY LABEL')) {
            target = s.closest('div[data-testid="stExpander"]');
            break;
        }
    }
    if (!target) {
        setTimeout(styleMyComponent, 200);  // Retry if DOM isn't ready
        return;
    }
    // Now directly manipulate the DOM
    target.style.cssText = 'border: 2px solid gold !important;';
    target.querySelectorAll('svg').forEach(svg => { svg.style.display = 'none'; });
})();
</script>
""", height=0)
```

## Key Principles
1. **`window.parent.document`** — JS in `components.html()` runs in an iframe, so use `window.parent.document` to access the main Streamlit DOM
2. **Find by text content or data-testid** — most reliable way to target specific components
3. **Always add a retry with setTimeout** — DOM may not be ready when script first runs
4. **Set `height=0`** — the components.html iframe should be invisible
5. **Use `.style.cssText`** — directly set styles on found elements rather than injecting CSS with class selectors
6. **For global styles** that apply to ALL instances of a component type, `st.markdown("<style>...")` with `data-testid` selectors (no wrapper class) is fine since those are global CSS selectors
