import React from 'react'

interface JsonDisplayProps {
  data: any
}

const JsonDisplay: React.FC<JsonDisplayProps> = ({ data }) => {
  const formatJson = (obj: any, indent = 0): JSX.Element[] => {
    const elements: JSX.Element[] = []
    
    if (typeof obj !== 'object' || obj === null) {
      return [<span key="value" className="json-value">{JSON.stringify(obj)}</span>]
    }

    const isArray = Array.isArray(obj)
    const entries = isArray ? obj.entries() : Object.entries(obj)
    
    elements.push(
      <span key="open-bracket" className="json-bracket">
        {isArray ? '[' : '{'}
      </span>
    )

    Array.from(entries).forEach(([key, value], index) => {
      const displayKey = isArray ? key : `"${key}"`
      elements.push(
        <div key={`entry-${index}`} className="json-entry" style={{ marginLeft: `${(indent + 1) * 20}px` }}>
          {!isArray && (
            <>
              <span className="json-key">{displayKey}</span>
              <span className="json-colon">: </span>
            </>
          )}
          {typeof value === 'object' && value !== null ? (
            <div className="json-nested">
              {formatJson(value, indent + 1)}
            </div>
          ) : (
            <span className="json-value">{JSON.stringify(value)}</span>
          )}
          {index < Object.keys(obj).length - 1 && <span className="json-comma">,</span>}
        </div>
      )
    })

    elements.push(
      <span key="close-bracket" className="json-bracket" style={{ marginLeft: `${indent * 20}px` }}>
        {isArray ? ']' : '}'}
      </span>
    )

    return elements
  }

  return (
    <div className="json-display">
      <pre className="json-content">
        {formatJson(data)}
      </pre>
    </div>
  )
}

export default JsonDisplay