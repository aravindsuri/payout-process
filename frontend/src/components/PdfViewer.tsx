import { useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`

interface PdfViewerProps {
  file: File
}

const PdfViewer: React.FC<PdfViewerProps> = ({ file }) => {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [fileUrl, setFileUrl] = useState<string>('')

  useEffect(() => {
    const url = URL.createObjectURL(file)
    setFileUrl(url)

    return () => {
      URL.revokeObjectURL(url)
    }
  }, [file])

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setPageNumber(1)
  }

  const goToPrevPage = () => {
    setPageNumber(pageNumber <= 1 ? 1 : pageNumber - 1)
  }

  const goToNextPage = () => {
    setPageNumber(pageNumber >= numPages ? numPages : pageNumber + 1)
  }

  return (
    <div className="pdf-viewer">
      <div className="pdf-controls">
        <button onClick={goToPrevPage} disabled={pageNumber <= 1}>
          Previous
        </button>
        <span>
          Page {pageNumber} of {numPages}
        </span>
        <button onClick={goToNextPage} disabled={pageNumber >= numPages}>
          Next
        </button>
      </div>

      <div className="pdf-document">
        <Document
          file={fileUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={(error) => console.error('Error loading PDF:', error)}
        >
          <Page pageNumber={pageNumber} width={400} />
        </Document>
      </div>
    </div>
  )
}

export default PdfViewer