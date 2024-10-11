import React, { useState } from 'react';
import axios from 'axios';
import EditModal from './EditModal';

const PdfTable = ({ pdfs, refreshPdfs }) => {
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedPdf, setSelectedPdf] = useState(null);

  const handleEdit = (pdf) => {
    setSelectedPdf(pdf);
    setEditModalOpen(true);
  };

  const handleUpdate = (updatedPdf) => {
    const formData = new FormData();
    formData.append('shop_name', updatedPdf.shop_name);
    formData.append('valid_from', updatedPdf.valid_from);
    formData.append('valid_to', updatedPdf.valid_to);
    if (updatedPdf.file) {
      formData.append('file', updatedPdf.file);
    }
    if (updatedPdf.file_url) {
      formData.append('file_url', updatedPdf.file_url);
    }

    axios.post(`http://127.0.0.1:5000/update/${updatedPdf.filename}`, formData)
      .then(response => {
        console.log(response.data);
        setEditModalOpen(false);
        refreshPdfs();
      })
      .catch(error => {
        console.error('Error updating file:', error);
      });
  };

  const handleDelete = (filename) => {
      axios.delete(`http://127.0.0.1:5000/delete/${filename}`)
        .then(response => {
          console.log(response.data);
          refreshPdfs();  // Refresh the PDF list after successful deletion
        })
        .catch(error => {
          console.error('Error deleting file:', error);
        });
    };

  const handleTriggerPipeline = (filename) => {
  axios.post(`http://127.0.0.1:5000/trigger_pipeline/${filename}`)
    .then(response => {
      console.log('Pipeline triggered:', response.data);
      refreshPdfs();  // Refresh the PDF list after triggering the pipeline
    })
    .catch(error => {
      console.error('Error triggering pipeline:', error);
    });
  };

  const isTriggerDisabled = (pdf) => {
    const today = new Date();
    const validFrom = new Date(pdf.valid_from);
    const validTo = new Date(pdf.valid_to);

    // Disable if already used
    if (pdf.used) return true;

    // Disable if the PDF is invalid and the current date is after the valid_to date
    if (!pdf.valid && today > validTo) return true;

    // Enable if the PDF is invalid but the current date is before valid_from
    if (!pdf.valid && today < validFrom) return false;

    // Otherwise, allow triggering
    return false;
  };


  const sortedPdfs = pdfs.sort((a, b) => new Date(a.valid_to) - new Date(b.valid_to));

  const isNearExpiry = (validToDate) => {
    const today = new Date();
    const validTo = new Date(validToDate);
    const timeDiff = validTo - today;
    const daysDiff = timeDiff / (1000 * 3600 * 24);
    return daysDiff <= 2;
  };

  return (
    <div>
      <table className="wider-table">
        <thead>
          <tr>
            <th>Shop Name</th>
            <th>File</th>
            <th>Valid From</th>
            <th>Valid To</th>
            <th>Upload Date</th>
            <th>Valid</th>
            <th>Edit</th>
            <th>Delete</th>
            <th>Split Pages</th>
          </tr>
        </thead>
        <tbody>
          {sortedPdfs.map((pdf, index) => (
            <tr key={index} className={isNearExpiry(pdf.valid_to) ? 'near-expiry' : ''}>
              <td>{pdf.shop_name}</td>
              <td><a href={`http://127.0.0.1:5000/uploads/${pdf.filename}`} target="_blank" rel="noopener noreferrer">{pdf.filename}</a></td>
              <td>{pdf.valid_from}</td>
              <td>{pdf.valid_to}</td>
              <td>{pdf.upload_date}</td>
              <td>{pdf.valid ? 'Valid' : 'Invalid'}</td> {/* Display validity */}
              <td><button onClick={() => handleEdit(pdf)}>Edit</button></td>
              <td><button onClick={() => handleDelete(pdf.filename)}>Delete</button></td>
              <td>
                <button
                    onClick={() => handleTriggerPipeline(pdf.filename)}
                    disabled={isTriggerDisabled(pdf)}
                >
                    {pdf.used ? 'Already Processed' : 'Trigger Pipeline'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {editModalOpen && (
        <EditModal
          pdf={selectedPdf}
          onClose={() => setEditModalOpen(false)}
          onSave={handleUpdate}
        />
      )}
    </div>
  );
};

export default PdfTable;
