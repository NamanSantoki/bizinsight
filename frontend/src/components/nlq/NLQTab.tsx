import React, { useState } from "react";
import axios from "axios";
import { Card, Input, Button, Spinner, Table } from "@/components/ui"; // assuming UI library

interface NLQResponse {
  query: string;
  sql: string;
  result: any[]; // array of rows
  contract_id?: string;
}

export const NLQTab: React.FC = () => {
  const [query, setQuery] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<NLQResponse | null>(null);
  const [error, setError] = useState<string>("");

  const runQuery = async () => {
    if (!query || !datasetId) {
      setError("Both query and dataset ID are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await axios.post<NLQResponse>("/api/v1/enterprise/nlq/", {
        query,
        dataset_id: datasetId,
      });
      setResponse(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <Card className="mb-4">
        <h2 className="text-xl font-semibold mb-2">Natural‑Language Query</h2>
        <Input
          placeholder="Dataset ID (e.g., sales_raw_v1)"
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
          className="mb-2"
        />
        <textarea
          placeholder="Enter your NL query…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full h-32 p-2 border rounded mb-2"
        />
        <Button onClick={runQuery} disabled={loading}>
          {loading ? <Spinner size="sm" /> : "Run Query"}
        </Button>
        {error && <p className="text-red-600 mt-2">{error}</p>}
      </Card>

      {response && (
        <Card>
          <h3 className="text-lg font-medium mb-2">Results</h3>
          <pre className="bg-gray-100 p-2 rounded mb-2">SQL: {response.sql}</pre>
          <Table>
            <thead>
              <tr>
                {response.result.length > 0 &&
                  Object.keys(response.result[0]).map((col) => (
                    <th key={col}>{col}</th>
                  ))}
              </tr>
            </thead>
            <tbody>
              {response.result.map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((val, i) => (
                    <td key={i}>{String(val)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}
    </div>
  );
};

