import { useState } from 'react'
import './App.css'
import PdfViewer from './components/PdfViewer'
import JsonDisplay from './components/JsonDisplay'

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [jsonData, setJsonData] = useState<any>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setJsonData(null)
  }

  const handleAnalyzePdf = async () => {
    if (!selectedFile) return

    setIsAnalyzing(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch('http://localhost:8001/api/analyze-pdf', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to analyze PDF')
      }

      const data = await response.json()
      setJsonData(data)
    } catch (error) {
      console.error('Error analyzing PDF:', error)
      alert('Error analyzing PDF. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleDebugExtract = async () => {
    if (!selectedFile) return

    setIsAnalyzing(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch('http://localhost:8001/api/debug-extract', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to debug extract PDF')
      }

      const data = await response.json()
      setJsonData(data)
    } catch (error) {
      console.error('Error in debug extraction:', error)
      alert('Error in debug extraction. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Payout Process</h1>
        <p>Upload a PDF and extract its structure using AI</p>
      </header>

      <div className="upload-section">
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
          className="file-input"
        />
        {selectedFile && (
          <div className="button-group">
            <button
              onClick={handleAnalyzePdf}
              disabled={isAnalyzing}
              className="analyze-button"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze PDF Structure'}
            </button>
            <button
              onClick={handleDebugExtract}
              disabled={isAnalyzing}
              className="debug-button"
            >
              {isAnalyzing ? 'Extracting...' : 'Debug Raw Extract'}
            </button>
          </div>
        )}
      </div>

      <div className="content-container">
        <div className="pdf-panel">
          <h3>PDF Viewer</h3>
          {selectedFile ? (
            <PdfViewer file={selectedFile} />
          ) : (
            <div className="placeholder">Select a PDF file to view</div>
          )}
        </div>

        <div className="json-panel">
          <h3>Extracted JSON Structure</h3>
          {jsonData ? (
            <JsonDisplay data={jsonData} />
          ) : (
            <div className="placeholder">
              {selectedFile ? 'Click "Analyze PDF Structure" to extract data' : 'Upload a PDF first'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
