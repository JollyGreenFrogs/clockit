import React from 'react'

function InvoiceGeneration() {
  return (
    <div className="invoice-generation">
      <div className="coming-soon-container" style={{
        textAlign: 'center',
        padding: '60px 20px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        color: 'white',
        margin: '20px 0'
      }}>
        <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🚧</div>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '15px', fontWeight: 'bold' }}>
          Invoice Generation
        </h2>
        <h3 style={{ fontSize: '1.8rem', marginBottom: '20px', fontWeight: '300' }}>
          Coming Soon
        </h3>
        <p style={{ fontSize: '1.1rem', opacity: '0.9', maxWidth: '600px', margin: '0 auto', lineHeight: '1.6' }}>
          We're working hard to bring you a powerful invoice generation system. 
          This feature will allow you to create professional invoices from your tracked time and tasks.
        </p>
        <div style={{ marginTop: '30px', padding: '20px', background: 'rgba(255,255,255,0.1)', borderRadius: '8px', display: 'inline-block' }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '1.2rem' }}>Coming Features:</h4>
          <ul style={{ listStyle: 'none', padding: '0', margin: '0', fontSize: '1rem' }}>
            <li style={{ margin: '8px 0' }}>📊 Automated invoice generation</li>
            <li style={{ margin: '8px 0' }}>💰 Multi-currency support</li>
            <li style={{ margin: '8px 0' }}>📄 PDF export functionality</li>
            <li style={{ margin: '8px 0' }}>⚙️ Customizable invoice templates</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default InvoiceGeneration