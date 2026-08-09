/**
 * MindMap Component - Integration wrapper for simple-mind-map
 */
import React, { useEffect, useRef, useState } from 'react'
import MindMap from 'simple-mind-map'

export interface MindMapNode {
  data: {
    text: string
    [key: string]: any
  }
  children?: MindMapNode[]
}

interface MindMapComponentProps {
  data: MindMapNode
  width?: number | string
  height?: number | string
  theme?: string
  layout?: string
  readonly?: boolean
  onNodeClick?: (node: any) => void
  onNodeDbClick?: (node: any) => void
}

export const MindMapComponent: React.FC<MindMapComponentProps> = ({
  data,
  width = '100%',
  height = '600px',
  theme = 'default',
  layout = 'logicalStructure',
  readonly = false,
  onNodeClick,
  onNodeDbClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const mindMapRef = useRef<any>(null)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (!containerRef.current) return

    try {
      // Initialize MindMap
      mindMapRef.current = new MindMap({
        el: containerRef.current,
        data: data,
        theme: theme,
        layout: layout,
        readonly: readonly,
      })

      // Register event handlers
      if (onNodeClick) {
        mindMapRef.current.on('node_click', onNodeClick)
      }
      if (onNodeDbClick) {
        mindMapRef.current.on('node_dblclick', onNodeDbClick)
      }

      return () => {
        if (mindMapRef.current) {
          mindMapRef.current.destroy()
        }
      }
    } catch (err) {
      setError(`Failed to initialize MindMap: ${err}`)
      console.error(err)
    }
  }, [])

  // Update data when props change
  useEffect(() => {
    if (mindMapRef.current && data) {
      mindMapRef.current.setData(data)
      mindMapRef.current.render()
    }
  }, [data])

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded">
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="mind-map-container border border-gray-200 rounded-lg"
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  )
}

export default MindMapComponent
