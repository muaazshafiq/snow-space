import fs from 'fs';
import { parse } from 'csv-parse/sync';
import { stringify } from 'csv-stringify/sync';

// Configuration
const MAX_ROWS_TO_PROCESS = null; // Set to null to process all rows
const RATE_LIMIT_MS = 1100; // Nominatim requires 1 request per second

// Helper function to get street address from coordinates
async function getStreetAddress(lat, lon) {
	try {
		const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`;
		const response = await fetch(url, {
			headers: {
				'User-Agent': 'SnowSpace/1.0'
			}
		});

		if (!response.ok) {
			console.error(`Failed to geocode ${lat}, ${lon}: ${response.status}`);
			return 'Address not found';
		}

		const data = await response.json();

		// Extract street address from the response
		const address = data.address;
		if (!address) return 'Address not found';

		// Build a readable street address
		const parts = [];
		if (address.house_number) parts.push(address.house_number);
		if (address.road) parts.push(address.road);
		else if (address.street) parts.push(address.street);
		else if (address.pedestrian) parts.push(address.pedestrian);

		// If we have a street, return it
		if (parts.length > 0) {
			return parts.join(' ');
		}

		// Fallback to display_name or a simpler format
		if (data.display_name) {
			const parts = data.display_name.split(',').slice(0, 2);
			return parts.join(',').trim();
		}

		return 'Address not found';
	} catch (error) {
		console.error(`Error geocoding ${lat}, ${lon}:`, error.message);
		return 'Error';
	}
}

// Delay helper (rate limiting)
function delay(ms) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

async function processCSV() {
	console.log('Reading CSV file...');
	const csvContent = fs.readFileSync('./ndsi_data.csv', 'utf-8');

	console.log('Parsing CSV...');
	const records = parse(csvContent, {
		columns: true,
		skip_empty_lines: true
	});

	console.log(`Total rows: ${records.length}`);

	// Filter rows with non-empty NDSI values
	const rowsWithNDSI = records.filter(row => row.ndsi && row.ndsi.trim() !== '');
	console.log(`Rows with NDSI values: ${rowsWithNDSI.length}`);

	// Determine how many to process
	const toProcess = MAX_ROWS_TO_PROCESS ? Math.min(MAX_ROWS_TO_PROCESS, rowsWithNDSI.length) : rowsWithNDSI.length;
	const estimatedTime = Math.ceil((toProcess * RATE_LIMIT_MS) / 1000 / 60);

	if (MAX_ROWS_TO_PROCESS && MAX_ROWS_TO_PROCESS < rowsWithNDSI.length) {
		console.log(`\nProcessing first ${toProcess} rows (limit set to ${MAX_ROWS_TO_PROCESS})`);
	} else {
		console.log(`\nProcessing all ${toProcess} rows`);
	}
	console.log(`Estimated time: ~${estimatedTime} minutes\n`);

	let processed = 0;
	let ndsiRowsProcessed = 0;

	for (const row of records) {
		// Only process rows with non-empty NDSI
		if (row.ndsi && row.ndsi.trim() !== '') {
			// Check if we've hit the limit
			if (MAX_ROWS_TO_PROCESS && ndsiRowsProcessed >= MAX_ROWS_TO_PROCESS) {
				row.street_address = 'Not processed (limit reached)';
			} else {
				const address = await getStreetAddress(row.lat, row.lon);
				row.street_address = address;
				ndsiRowsProcessed++;

				// Progress update every 10 rows
				if (ndsiRowsProcessed % 10 === 0) {
					console.log(`Processed ${ndsiRowsProcessed}/${toProcess} rows...`);
				}

				// Rate limiting: 1 request per second (Nominatim requirement)
				await delay(RATE_LIMIT_MS);
			}
			processed++;
		} else {
			// Leave address empty for rows without NDSI
			row.street_address = '';
		}
	}

	console.log(`\nCompleted! Processed ${processed} addresses.`);
	console.log('Writing updated CSV...');

	// Write back to CSV
	const output = stringify(records, {
		header: true,
		columns: ['seg_id', 'vertex_seq', 'lon', 'lat', 'traffic_score', 'ndsi', 'used_image_date', 'street_address']
	});

	fs.writeFileSync('./ndsi_data.csv', output);
	console.log('Done! CSV updated with street addresses.');
}

// Run the script
processCSV().catch(console.error);
