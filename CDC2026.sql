USE CDC2026;

SELECT 
      date_received
    , product
    , COALESCE(sub_product, 'Unknown') AS sub_product
    , COALESCE(issue, 'Unknown') AS issue
    , COALESCE(sub_issue, 'Unknown') AS sub_issue
    , COALESCE(company, 'Unknown') AS company
    , COALESCE(state, 'Unknown') AS state
    , COALESCE(ZIP_code, 'Unknown') AS ZIP_code
    , Submitted_via
    , Date_sent_to_company
    , COALESCE(Company_response_to_consumer, 'Unknown') AS Company_response_to_consumer
    , timely_response
    , complaint_id
FROM complaints
WHERE state IN (
      'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
      'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
      'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
      'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
      'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI'
);