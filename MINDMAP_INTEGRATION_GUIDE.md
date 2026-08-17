# Mind Map Integration Guide for FieldMind

## Overview

**simple-mind-map** is a powerful JavaScript library for creating interactive mind maps in web applications. It's framework-agnostic and can be integrated into React, Vue, or vanilla JavaScript projects.

## NPM Package Information

- **Package Name**: `simple-mind-map`
- **Latest Version**: 0.14.0-fix.3
- **License**: MIT
- **Documentation**: https://wanglin2.github.io/mind-map-docs/
- **GitHub**: https://github.com/wanglin2/mind-map

## Features

1. **Framework Agnostic**: Works with React, Vue, Angular, or vanilla JS
2. **Rich Node Content**: Text, images, links, icons, notes, tags, formulas
3. **Multiple Layouts**: Mind map, logical structure, org chart, timeline, fishbone
4. **Export Formats**: PNG, SVG, PDF, XMind, FreeMind, Markdown
5. **Import Formats**: XMind, FreeMind, Markdown, JSON
6. **Themes**: Hundreds of built-in themes + custom theme support
7. **Interactive**: Drag & drop, zoom, pan, minimap
8. **Collaborative**: WebRTC support via y-webrtc

## Installation

For FieldMind Web (React):
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-web
npm install simple-mind-map --save
```

## Basic Integration Example (React)

```tsx
import React, { useEffect, useRef } from 'react';
import MindMap from 'simple-mind-map';

const MindMapComponent: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mindMapRef = useRef<any>(null);

  useEffect(() => {
    if (containerRef.current && !mindMapRef.current) {
      mindMapRef.current = new MindMap({
        el: containerRef.current,
        data: {
          data: {
            text: 'Root Node'
          },
          children: [
            {
              data: {
                text: 'Child 1'
              },
              children: []
            },
            {
              data: {
                text: 'Child 2'
              },
              children: []
            }
          ]
        },
        theme: 'default',
        layout: 'logicalStructure'
      });
    }

    return () => {
      if (mindMapRef.current) {
        mindMapRef.current.destroy();
      }
    };
  }, []);

  return (
    <div 
      ref={containerRef} 
      style={{ width: '100%', height: '600px' }}
    />
  );
};

export default MindMapComponent;
```

## Integration Points in FieldMind

### 1. Project Knowledge Context Visualization

**Location**: Project Dashboard → Knowledge Context Tab

**Use Case**: Visualize the hierarchical relationships between knowledge contexts

```tsx
// KnowledgeContextMindMap.tsx
interface KnowledgeContext {
  id: number;
  name: string;
  description: string;
  parent_id?: number;
  children?: KnowledgeContext[];
}

const convertContextToMindMapData = (context: KnowledgeContext) => {
  return {
    data: {
      text: context.name,
      note: context.description,
      id: context.id
    },
    children: context.children?.map(convertContextToMindMapData) || []
  };
};
```

### 2. Document Structure Visualization

**Location**: Document Detail Page → Structure View

**Use Case**: Show document outline as a mind map

```tsx
// DocumentMindMap.tsx
interface DocumentSection {
  title: string;
  level: number;
  content: string;
  subsections: DocumentSection[];
}

const convertDocumentToMindMap = (sections: DocumentSection[]) => {
  // Convert markdown headings to mind map nodes
};
```

### 3. Chat Thinking Process Visualization

**Location**: Enhanced Chat → Thinking Process Tab

**Use Case**: Visualize AI's reasoning steps as a mind map

```tsx
// ThinkingProcessMindMap.tsx
interface ThinkingStep {
  step: string;
  reasoning: string;
  sub_steps?: ThinkingStep[];
}

const visualizeThinking = (thinkingProcess: string) => {
  // Parse thinking process and convert to mind map
};
```

### 4. Memory Network Visualization

**Location**: Project Dashboard → Memory Map

**Use Case**: Show connections between memory entries

```tsx
// MemoryNetworkMindMap.tsx
interface MemoryNode {
  id: number;
  content: string;
  importance: number;
  related_memories: number[];
}

const buildMemoryMap = (memories: MemoryNode[]) => {
  // Build network of interconnected memories
};
```

## Advanced Features

### Export Functionality

```typescript
// Export as PNG
mindMap.export({
  type: 'png',
  name: 'knowledge-context-map',
  quality: 1.0
});

// Export as JSON (for saving)
const data = mindMap.getData();
localStorage.setItem('mindmap-data', JSON.stringify(data));

// Export as Markdown
mindMap.export({
  type: 'md',
  name: 'knowledge-structure'
});
```

### Import Functionality

```typescript
// Import from JSON
const savedData = JSON.parse(localStorage.getItem('mindmap-data'));
mindMap.setData(savedData);

// Import from XMind file
mindMap.import({
  type: 'xmind',
  file: xmindFile
});
```

### Custom Themes

```typescript
mindMap.setTheme({
  backgroundColor: '#f5f5f5',
  nodeBackgroundColor: '#ffffff',
  nodeBorderColor: '#1890ff',
  nodeTextColor: '#333333',
  lineColor: '#1890ff',
  lineWidth: 2
});
```

## API Integration

### Backend Endpoint for Saving Mind Maps

```python
# app/api/v1/mind_maps.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/projects/{project_id}/mind-maps")
async def save_mind_map(
    project_id: int,
    mind_map_data: dict,
    db: Session = Depends(get_db)
):
    """Save mind map visualization data"""
    # Save to project_contexts or new mind_maps table
    pass

@router.get("/projects/{project_id}/mind-maps/{map_id}")
async def get_mind_map(
    project_id: int,
    map_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve saved mind map"""
    pass
```

## Integration Checklist

- [ ] Install `simple-mind-map` package in fieldmind-web
- [ ] Create MindMapComponent wrapper component
- [ ] Implement knowledge context visualization
- [ ] Add document structure mind map view
- [ ] Integrate thinking process visualization
- [ ] Create memory network visualization
- [ ] Add export/import functionality
- [ ] Implement save/load from backend
- [ ] Add custom FieldMind theme
- [ ] Add toolbar for mind map operations (zoom, pan, reset)

## Dependencies

```json
{
  "dependencies": {
    "simple-mind-map": "^0.14.0-fix.3"
  }
}
```

Core dependencies (automatically installed):
- @svgdotjs/svg.js: SVG rendering
- eventemitter3: Event system
- jszip: Export functionality
- katex: Math formula support
- quill: Rich text editing
- yjs + y-webrtc: Collaborative editing

## Resources

- **Documentation**: https://wanglin2.github.io/mind-map-docs/
- **Online Demo**: https://web.sxmind.cn/
- **GitHub**: https://github.com/wanglin2/mind-map
- **NPM**: https://www.npmjs.com/package/simple-mind-map

## Next Steps

1. Set up fieldmind-web React project (currently only README exists)
2. Install simple-mind-map package
3. Create reusable MindMapComponent
4. Implement first visualization (knowledge context map)
5. Connect to backend API for data persistence
6. Add to project dashboard UI

---

**Status**: ✅ Package identified and documented, ready for integration
**Priority**: Medium - Enhances visualization capabilities
**Estimated Integration Time**: 2-3 days for basic implementation
