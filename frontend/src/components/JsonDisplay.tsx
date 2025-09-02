import React, { useState } from 'react'

interface JsonDisplayProps {
  data: any
}

const JsonDisplay: React.FC<JsonDisplayProps> = ({ data }) => {
  const [viewMode, setViewMode] = useState<'formatted' | 'raw'>('formatted')
  
  const formatJsonString = (obj: any): string => {
    try {
      return JSON.stringify(obj, null, 2)
    } catch (error) {
      return String(obj)
    }
  }

  const renderFormattedJson = (obj: any, level = 0): React.ReactNode => {
    if (obj === null) return <span className="json-null">null</span>
    if (typeof obj === 'boolean') return <span className="json-boolean">{obj.toString()}</span>
    if (typeof obj === 'number') return <span className="json-number">{obj}</span>
    if (typeof obj === 'string') return <span className="json-string">"{obj}"</span>
    
    if (Array.isArray(obj)) {
      if (obj.length === 0) return <span className="json-bracket">[]</span>
      return (
        <div className="json-array">
          <span className="json-bracket">[</span>
          {obj.map((item, index) => (
            <div key={index} className="json-array-item" style={{ marginLeft: `${(level + 1) * 16}px` }}>
              {renderFormattedJson(item, level + 1)}
              {index < obj.length - 1 && <span className="json-comma">,</span>}
            </div>
          ))}
          <span className="json-bracket" style={{ marginLeft: `${level * 16}px` }}>]</span>
        </div>
      )
    }
    
    if (typeof obj === 'object') {
      const entries = Object.entries(obj)
      if (entries.length === 0) return <span className="json-bracket">{}</span>
      return (
        <div className="json-object">
          <span className="json-bracket">{'{'}</span>
          {entries.map(([key, value], index) => (
            <div key={key} className="json-object-entry" style={{ marginLeft: `${(level + 1) * 16}px` }}>
              <span className="json-key">"{key}"</span>
              <span className="json-colon">: </span>
              {renderFormattedJson(value, level + 1)}
              {index < entries.length - 1 && <span className="json-comma">,</span>}
            </div>
          ))}
          <span className="json-bracket" style={{ marginLeft: `${level * 16}px` }}>{'}'}</span>
        </div>
      )
    }
    
    return <span>{String(obj)}</span>
  }

  const getValidationStatus = () => {
    // First check for new comprehensive signature details
    if (data?.signature_details?.signature_validation) {
      const validation = data.signature_details.signature_validation
      return {
        status: validation.validation_status,
        message: `${validation.completed_signatures || 0}/${validation.total_signature_fields || 0} signatures complete`,
        notes: validation.validation_notes
      }
    }
    // Fallback to old signature validation structure
    if (data?.signature_validation) {
      const validation = data.signature_validation
      return {
        status: validation.validation_status,
        message: `${validation.completed_signatures || 0}/${validation.total_signature_fields || 0} signatures complete`,
        notes: validation.validation_notes
      }
    }
    return null
  }

  const validationInfo = getValidationStatus()

  return (
    <div className="json-display">
      {validationInfo && (
        <div className={`validation-banner validation-${validationInfo.status?.toLowerCase()}`}>
          <div className="validation-header">
            <span className="validation-icon">
              {validationInfo.status === 'COMPLETE' ? '✅' : 
               validationInfo.status === 'INCOMPLETE' ? '❌' : '⚠️'}
            </span>
            <span className="validation-status">{validationInfo.status}</span>
            <span className="validation-message">{validationInfo.message}</span>
          </div>
          {validationInfo.notes && (
            <div className="validation-notes">{validationInfo.notes}</div>
          )}
        </div>
      )}
      <div className="json-controls">
        <button 
          className={viewMode === 'formatted' ? 'active' : ''} 
          onClick={() => setViewMode('formatted')}
        >
          Formatted
        </button>
        <button 
          className={viewMode === 'raw' ? 'active' : ''} 
          onClick={() => setViewMode('raw')}
        >
          Raw JSON
        </button>
      </div>
      <div className="json-content-wrapper">
        {viewMode === 'formatted' ? (
          <div className="json-formatted">
            {renderFormattedJson(data)}
          </div>
        ) : (
          <pre className="json-raw">
            {formatJsonString(data)}
          </pre>
        )}
      </div>
    </div>
  )
}

export default JsonDisplay