import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [prescription, setPrescription] = useState(null);

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    console.log("Sending text:", input);
    try {
      const response = await axios.post('http://localhost:5000/chat', { text: input }, {
        headers: { 'Content-Type': 'application/json' },
      });
      console.log("Response from backend:", response.data);

      // Extract the response text from response.data
      const responseText = response.data.response;

      // Update the messages state with the user input and the chatbot's response
      setMessages([...messages, { role: 'user', content: input }, { role: 'assistant', content: responseText }]);

      // Parse the response into a structured prescription form
      try {
        const parsedPrescription = JSON.parse(responseText);
        setPrescription(parsedPrescription);
      } catch (error) {
        console.error("Failed to parse prescription:", error);
      }

      setInput('');
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Chatbot</h1>
      <div style={{ marginBottom: '20px' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: '10px', padding: '10px', border: '1px solid #ccc', borderRadius: '5px' }}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleTextSubmit} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          style={{ flex: 1, padding: '10px', fontSize: '16px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <button type="submit" style={{ padding: '10px 20px', fontSize: '16px', borderRadius: '5px', border: 'none', backgroundColor: '#007bff', color: '#fff', cursor: 'pointer' }}>
          Send
        </button>
      </form>

      {prescription && (
        <div style={{ marginTop: '20px', padding: '20px', border: '1px solid #ccc', borderRadius: '5px' }}>
          <h2>Prescription Form</h2>
          <h3>Diagnosis Information</h3>
          <p><strong>Diagnosis:</strong> {prescription.DiagnosisInformation.Diagnosis}</p>
          <p><strong>Medicine:</strong> {prescription.DiagnosisInformation.Medicine}</p>

          <h3>Medication Details</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ border: '1px solid #ccc', padding: '10px' }}>Dose</th>
                <th style={{ border: '1px solid #ccc', padding: '10px' }}>Unit</th>
                <th style={{ border: '1px solid #ccc', padding: '10px' }}>Route</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid #ccc', padding: '10px' }}>{prescription.MedicationDetails.Dose.Quantity}</td>
                <td style={{ border: '1px solid #ccc', padding: '10px' }}>{prescription.MedicationDetails.Dose.Unit}</td>
                <td style={{ border: '1px solid #ccc', padding: '10px' }}>{prescription.MedicationDetails.Route.Unit}</td>
              </tr>
            </tbody>
          </table>

          <p><strong>Frequency:</strong> {prescription.MedicationDetails.Dose.Frequency}</p>
          <p><strong>Duration:</strong> {prescription.MedicationDetails.Duration.Days} days</p>
          <p><strong>Refill:</strong> {prescription.MedicationDetails.Route.Refill}</p>
          <p><strong>Pharmacy:</strong> {prescription.MedicationDetails.Route.Pharmacy}</p>

          <h3>Description</h3>
          <p>{prescription.Description}</p>

          <p><strong>Creation Time:</strong> {new Date().toLocaleString()}</p>
        </div>
      )}
    </div>
  );
}

export default App;