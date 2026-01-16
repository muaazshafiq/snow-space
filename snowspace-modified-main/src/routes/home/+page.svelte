<script>
	import StreetCard from '$lib/components/StreetCard.svelte';
	import { onMount } from 'svelte';

	let radius = $state(5);
	let filterMode = $state('priority-high');
	let isFilterOpen = $state(false);
	let totalEarnings = $state(0);

	const USER_LOCATION = { lat: 43.6850, lng: -79.7596 };

	let mapElement;
	let map;
	let markers = [];
	let verifyingTask = $state(null);
	let taskSuccess = $state(false);
	let selectedStreetId = $state(null);
	let showCashOutModal = $state(false);
	let cashOutSuccess = $state(false);

	const filterOptions = [
		{ value: 'alpha-asc', label: 'A-Z' },
		{ value: 'alpha-desc', label: 'Z-A' },
		{ value: 'payout-high', label: 'Payout (High-Low)' },
		{ value: 'payout-low', label: 'Payout (Low-High)' },
		{ value: 'priority-high', label: 'Priority (High-Low)' },
		{ value: 'priority-low', label: 'Priority (Low-High)' }
	];

	function toggleFilter() {
		isFilterOpen = !isFilterOpen;
	}

	function selectFilter(value) {
		filterMode = value;
		isFilterOpen = false;
	}

	// Close dropdown when clicking outside
	function handleClickOutside(e) {
		if (!e.target.closest('.filter-container')) {
			isFilterOpen = false;
		}
	}

	function handleCashOut() {
		if (totalEarnings === 0) return;
		showCashOutModal = true;
	}

	function confirmCashOut() {
		showCashOutModal = false;
		cashOutSuccess = true;
		totalEarnings = 0;

		setTimeout(() => {
			cashOutSuccess = false;
		}, 3000);
	}

	function cancelCashOut() {
		showCashOutModal = false;
	}

	// Calculate realistic dynamic price based on multiple factors
	function calculatePrice(basePriority, createdAt, coordinates = null, trafficScore = 0, ndsi = 0) {
		// Base rates
		const BASE_RATE_PER_METER = 0.15; // $0.15 per meter of street
		const STREET_LENGTH = 200; // Average street segment ~200m

		// Snow depth multiplier (NDSI: -1 to 1, where higher = more snow)
		const snowDepthFactor = Math.max(1, 1 + (ndsi * 2)); // 1x to 3x multiplier

		// Traffic urgency multiplier (0-1 traffic score)
		const trafficMultiplier = 1 + (trafficScore * 1.5); // 1x to 2.5x

		// Priority urgency (0-10 scale)
		const priorityMultiplier = 1 + (basePriority / 10) * 0.8; // 1x to 1.8x

		// Time-based urgency (grows over time)
		const hoursElapsed = (Date.now() - createdAt) / (1000 * 60 * 60);
		const urgencyBonus = Math.min(hoursElapsed * 5, 50); // Max $50 bonus

		// Time of day multiplier (higher pay at night/early morning)
		const hour = new Date().getHours();
		const timeOfDayMultiplier = (hour >= 22 || hour <= 6) ? 1.5 : 1.0;

		// Distance penalty/bonus (closer = slight bonus for convenience)
		let distanceMultiplier = 1.0;
		if (coordinates) {
			const distance = calculateDistance(
				USER_LOCATION.lat,
				USER_LOCATION.lng,
				coordinates.lat,
				coordinates.lng
			);
			distanceMultiplier = distance < 1 ? 1.2 : (distance < 3 ? 1.0 : 0.9);
		}

		// Calculate final price
		const basePrice = BASE_RATE_PER_METER * STREET_LENGTH;
		const multipliedPrice = basePrice * snowDepthFactor * trafficMultiplier * priorityMultiplier * timeOfDayMultiplier * distanceMultiplier;
		const finalPrice = multipliedPrice + urgencyBonus;

		// Apply realistic min/max caps
		return Math.round(Math.max(20, Math.min(finalPrice, 500)));
	}

	// Color earnings based on amount (more green = higher)
	function getEarningsColor(amount) {
		if (amount === 0) return '#666';
		const intensity = Math.min(amount / 1000, 1); // Scale to 1000
		const r = Math.round(16 - intensity * 6);
		const g = Math.round(185 - intensity * 65);
		const b = Math.round(129 - intensity * 100);
		return `rgb(${r}, ${g}, ${b})`;
	}

	// Color average payout (more green = higher)
	function getPayoutColor(avgPayout) {
		const intensity = Math.min(avgPayout / 200, 1); // Scale to 200
		const r = Math.round(107 - intensity * 97);
		const g = Math.round(114 - intensity * -71);
		const b = Math.round(128 - intensity * -1);
		return `rgb(${r}, ${g}, ${b})`;
	}

	// Color priority score (0 = green, 10 = red) - same as in StreetCard
	function getPriorityColor(score) {
		const clampedScore = Math.max(0, Math.min(10, score));
		const ratio = clampedScore / 10;
		const r = Math.round(10 + ratio * (239 - 10));
		const g = Math.round(185 - ratio * (185 - 68));
		const b = Math.round(129 - ratio * (129 - 68));
		return `rgb(${r}, ${g}, ${b})`;
	}

	async function handleCardComplete(price, isCompleted, streetData) {
		if (isCompleted) {
			verifyingTask = { streetName: streetData.streetName };

			await new Promise(resolve => setTimeout(resolve, 5000));

			verifyingTask = null;
			taskSuccess = true;

			if (typeof window !== 'undefined' && window.confetti) {
				window.confetti({
					particleCount: 100,
					spread: 70,
					origin: { y: 0.6 }
				});
			}

			totalEarnings += price;
			streetData.priorityScore = 0;
			streetData.completed = true;

			// Update all map points for this street
			allMapPoints.forEach(point => {
				if (point.streetName === streetData.streetName) {
					point.priorityScore = 0;
				}
			});

			setTimeout(() => {
				taskSuccess = false;
			}, 2000);
		} else {
			totalEarnings -= price;
		}
	}

	// Calculate distance between two coordinates in kilometers using Haversine formula
	function calculateDistance(lat1, lng1, lat2, lng2) {
		const R = 6371; // Earth's radius in kilometers
		const dLat = (lat2 - lat1) * Math.PI / 180;
		const dLng = (lng2 - lng1) * Math.PI / 180;
		const a =
			Math.sin(dLat / 2) * Math.sin(dLat / 2) +
			Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
			Math.sin(dLng / 2) * Math.sin(dLng / 2);
		const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
		return R * c; // Distance in kilometers
	}

	// Convert lat/lng to SVG coordinates
	// Map bounds: Brampton area (roughly 43.6-43.8 lat, -79.9 to -79.6 lng)
	function latLngToSVG(lat, lng) {
		// Map boundaries for Brampton area
		const minLat = 43.6;
		const maxLat = 43.8;
		const minLng = -79.9;
		const maxLng = -79.6;

		// Normalize to 0-1 range
		const x = (lng - minLng) / (maxLng - minLng);
		const y = 1 - (lat - minLat) / (maxLat - minLat); // Invert Y for SVG coordinates

		// Map to SVG viewBox (0-430 width, 0-932 height)
		return {
			x: x * 430,
			y: y * 932
		};
	}

	// Load and process CSV data
	const now = Date.now();
	let streetsData = $state([]);
	let allMapPoints = $state([]); // Store all points
	let hoveredPoint = $state(null);
	let isDataLoading = $state(true);

	onMount(() => {
		generateSyntheticData();
		initMap();
	});

	function initMap() {
		if (typeof window === 'undefined' || !window.L) return;

		map = window.L.map(mapElement, {
			center: [USER_LOCATION.lat, USER_LOCATION.lng],
			zoom: 12,
			zoomControl: true
		});

		window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '© OpenStreetMap'
		}).addTo(map);
	}

	let radiusCircle;

	function updateMapMarkers() {
		if (!map || !window.L) return;

		// Update radius circle with animation
		if (radiusCircle) map.removeLayer(radiusCircle);
		radiusCircle = window.L.circle([USER_LOCATION.lat, USER_LOCATION.lng], {
			radius: radius * 1000,
			color: '#4DB6ED',
			fillOpacity: 0.1,
			className: 'radius-circle-animate'
		}).addTo(map);

		// Get current points that should be visible
		const visiblePoints = mapPoints();
		const visiblePointIds = new Set(visiblePoints.map(p => p.id));

		// Fade out and remove markers that are no longer visible
		markers = markers.filter(markerData => {
			if (!visiblePointIds.has(markerData.pointId)) {
				// Fade out animation
				const element = markerData.marker.getElement();
				if (element) {
					element.style.transition = 'opacity 0.15s ease-out';
					element.style.opacity = '0';
					setTimeout(() => {
						map.removeLayer(markerData.marker);
					}, 150);
				} else {
					map.removeLayer(markerData.marker);
				}
				return false;
			}
			return true;
		});

		// Get existing marker IDs
		const existingIds = new Set(markers.map(m => m.pointId));

		// Add new markers with fade in animation
		visiblePoints.forEach(point => {
			if (!existingIds.has(point.id)) {
				const color = getPriorityColor(point.priorityScore);
				const marker = window.L.circleMarker([point.coordinates.lat, point.coordinates.lng], {
					radius: 6,
					fillColor: color,
					color: '#fff',
					weight: 1,
					fillOpacity: 0,
					className: 'map-marker-animate'
				}).addTo(map);

				// Fade in animation
				setTimeout(() => {
					const element = marker.getElement();
					if (element) {
						element.style.transition = 'opacity 0.15s ease-in';
						element.style.opacity = '1';
					}
					marker.setStyle({ fillOpacity: 0.8 });
				}, 10);

				const price = calculatePrice(point.priorityScore, point.createdAt, point.coordinates, Math.min(point.rawScore / 100, 1), 0.5);
				marker.bindPopup(`<strong>${point.streetName}</strong><br>Payout: $${price}<br>Priority: ${point.priorityScore}`);
				marker.on('click', () => {
					const street = streetsData.find(s => s.streetName === point.streetName);
					if (street) selectedStreetId = street.id;
				});

				markers.push({ marker, pointId: point.id });
			}
		});
	}

	$effect(() => {
		radius;
		updateMapMarkers();
	});

	$effect(() => {
		if (selectedStreetId) {
			document.getElementById(`street-${selectedStreetId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
		}
	});

	function generateSyntheticData() {
		// Street name components for variety
		const streetPrefixes = ['Main', 'Maple', 'Oak', 'Pine', 'Cedar', 'Elm', 'Queen', 'King', 'Victoria', 'Wellington', 'Church', 'Mill', 'Bridge', 'Park', 'Hill', 'Lake', 'River', 'Forest', 'Meadow', 'Spring', 'Willow', 'Birch', 'Ash', 'Chestnut', 'Walnut'];
		const streetTypes = ['Street', 'Avenue', 'Road', 'Drive', 'Lane', 'Court', 'Crescent', 'Boulevard', 'Way', 'Place'];

		const generatedPoints = [];
		const numPoints = 400; // Generate many more points for natural scatter

		for (let i = 0; i < numPoints; i++) {
			// Completely random radius within 5km, but bias towards outer areas
			// Use square root to get more even area distribution
			const randomRadius = Math.sqrt(Math.random()) * 5;

			// Completely random angle
			const randomAngle = Math.random() * 2 * Math.PI;

			// Convert polar to lat/lng
			const lat = USER_LOCATION.lat + (randomRadius * Math.cos(randomAngle)) / 111.32;
			const lng = USER_LOCATION.lng + (randomRadius * Math.sin(randomAngle)) / (111.32 * Math.cos(USER_LOCATION.lat * Math.PI / 180));

			// Generate random street name
			const prefix = streetPrefixes[Math.floor(Math.random() * streetPrefixes.length)];
			const type = streetTypes[Math.floor(Math.random() * streetTypes.length)];
			const number = Math.floor(Math.random() * 900) + 100;
			const streetName = `${number} ${prefix} ${type}`;

			// Generate random priority score (1-10)
			const priorityScore = parseFloat((Math.random() * 9 + 1).toFixed(1));

			// Create point data
			generatedPoints.push({
				id: `point-${i}`,
				coordinates: { lat, lng },
				streetName,
				priorityScore,
				createdAt: now,
				completed: false,
				rawScore: priorityScore * 10
			});
		}

		// Group by street name and take one per street (for street cards)
		const streetMap = new Map();
		generatedPoints.forEach(point => {
			const existing = streetMap.get(point.streetName);
			if (!existing || point.priorityScore > existing.priorityScore) {
				streetMap.set(point.streetName, point);
			}
		});

		streetsData = Array.from(streetMap.values()).map((street, idx) => ({
			...street,
			id: idx + 1
		}));

		// Store all map points for visualization
		allMapPoints = generatedPoints;

		isDataLoading = false;
		console.log(`Generated ${streetsData.length} unique street cards and ${allMapPoints.length} total map points`);
	}

	// Calculate current prices for all streets
	let streetsWithPrices = $derived(() => {
		// Trigger recalculation when priceUpdateTrigger changes
		priceUpdateTrigger;
		return streetsData.map(street => {
			// Find the original data point to get traffic and ndsi
			const dataPoint = allMapPoints.find(p => p.id === street.id);
			const trafficScore = dataPoint?.rawScore ? Math.min(dataPoint.rawScore / 100, 1) : 0;
			const ndsi = 0.5; // Default snow depth factor (could be dynamic)

			return {
				...street,
				price: calculatePrice(
					street.priorityScore,
					street.createdAt,
					street.coordinates,
					trafficScore,
					ndsi
				)
			};
		});
	});

	// Filtered and sorted streets based on selected filter and radius
	let streets = $derived(() => {
		// First filter by radius distance from user location and exclude completed
		const withinRadius = streetsWithPrices().filter(street => {
			const distance = calculateDistance(
				USER_LOCATION.lat,
				USER_LOCATION.lng,
				street.coordinates.lat,
				street.coordinates.lng
			);
			return distance <= radius && !street.completed;
		});

		// Then sort based on selected filter
		const sorted = [...withinRadius];

		switch (filterMode) {
			case 'alpha-asc':
				return sorted.sort((a, b) => a.streetName.localeCompare(b.streetName));
			case 'alpha-desc':
				return sorted.sort((a, b) => b.streetName.localeCompare(a.streetName));
			case 'payout-high':
				return sorted.sort((a, b) => b.price - a.price);
			case 'payout-low':
				return sorted.sort((a, b) => a.price - b.price);
			case 'priority-high':
				return sorted.sort((a, b) => b.priorityScore - a.priorityScore);
			case 'priority-low':
				return sorted.sort((a, b) => a.priorityScore - b.priorityScore);
			default:
				return sorted;
		}
	});

	// Filter map points by radius for performance (only render visible points)
	let mapPoints = $derived(() => {
		return allMapPoints.filter(point => {
			const distance = calculateDistance(
				USER_LOCATION.lat,
				USER_LOCATION.lng,
				point.coordinates.lat,
				point.coordinates.lng
			);
			return distance <= radius && point.priorityScore > 0;
		});
	});

	// Calculate statistics for peek mode (only for streets within radius)
	let stats = $derived(() => {
		const incomplete = streets().filter(s => !s.completed);
		const avgPayout = incomplete.length > 0
			? Math.round(incomplete.reduce((sum, s) => sum + s.price, 0) / incomplete.length)
			: 0;
		const avgPriority = incomplete.length > 0
			? (incomplete.reduce((sum, s) => sum + s.priorityScore, 0) / incomplete.length).toFixed(1)
			: 0;

		return {
			earnings: totalEarnings,
			jobCount: incomplete.length,
			avgPayout,
			avgPriority: parseFloat(avgPriority)
		};
	});

	// Update prices every minute with countdown
	let priceUpdateTrigger = $state(0);
	let countdown = $state(60);

	$effect(() => {
		// Countdown every second
		const countdownInterval = setInterval(() => {
			countdown -= 1;
			if (countdown <= 0) {
				countdown = 60;
				priceUpdateTrigger = Date.now();
			}
		}, 1000);

		return () => clearInterval(countdownInterval);
	});

</script>

<div class="page-wrapper">
	<div class="left-panel">
		<div class="stats-header">
			<h2>Earned <span style="color: {getEarningsColor(totalEarnings)};">${totalEarnings}</span></h2>
			<div class="filter-container">
				<button class="filter-icon-button" onclick={toggleFilter}>
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
						<path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zM3.5 5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1 0-1zM5 8.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm2 3a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 0 1h-1a.5.5 0 0 1-.5-.5z"/>
					</svg>
				</button>
				{#if isFilterOpen}
					<div class="filter-dropdown-menu">
						{#each filterOptions as option}
							<button class="filter-option" class:active={filterMode === option.value} onclick={() => selectFilter(option.value)}>
								{option.label}
							</button>
						{/each}
					</div>
				{/if}
			</div>
		</div>
		<div class="radius-control">
			<label>Radius: {radius}km</label>
			<input type="range" min="0.25" max="6" step="0.25" bind:value={radius} />
		</div>
		<p>{countdown}s to boost</p>
		<div class="street-list">
			{#each streets() as street}
				<div id="street-{street.id}" class:highlighted={selectedStreetId === street.id}>
					<StreetCard
						coordinates={street.coordinates}
						streetName={street.streetName}
						price={street.price}
						priorityScore={street.priorityScore}
						onComplete={(price, isCompleted) => {
							const streetData = streetsData.find(s => s.id === street.id);
							if (streetData) {
								handleCardComplete(price, isCompleted, streetData);
							}
						}}
					/>
				</div>
			{/each}
		</div>
	</div>
	<div class="right-panel">
		<button class="cash-out-button" onclick={handleCashOut} disabled={totalEarnings === 0}>
			Cash Out ${totalEarnings}
		</button>
		<div bind:this={mapElement} class="map"></div>
	</div>

	{#if verifyingTask}
		<div class="modal">
			<div class="modal-content">
				<div class="spinner"></div>
				<h3>Verifying with satellite...</h3>
				<p>{verifyingTask.streetName}</p>
			</div>
		</div>
	{/if}

	{#if taskSuccess}
		<div class="modal">
			<div class="modal-content success">
				<div class="checkmark">✓</div>
				<h3>Task Successfully Done!</h3>
			</div>
		</div>
	{/if}

	{#if showCashOutModal}
		<div class="modal">
			<div class="modal-content cash-out">
				<h3>Cash Out</h3>
				<p class="cash-out-amount">${totalEarnings}</p>
				<div class="cash-out-info">
					<label for="bank-account">Bank Account (optional)</label>
					<input type="text" id="bank-account" placeholder="Enter bank account (optional for demo)" />
				</div>
				<div class="modal-buttons">
					<button class="cancel-button" onclick={cancelCashOut}>Cancel</button>
					<button class="confirm-button" onclick={confirmCashOut}>Confirm Cash Out</button>
				</div>
			</div>
		</div>
	{/if}

	{#if cashOutSuccess}
		<div class="modal">
			<div class="modal-content success">
				<div class="checkmark">✓</div>
				<h3>Money Sent!</h3>
				<p>Your earnings have been transferred.</p>
			</div>
		</div>
	{/if}
</div>

<svelte:window onclick={handleClickOutside} />

<style>
	.page-wrapper {
		display: flex;
		height: 100vh;
	}

	.left-panel {
		width: 40%;
		padding: 24px;
		overflow-y: auto;
		background: #fff;
	}

	.left-panel::-webkit-scrollbar {
		width: 8px;
		display: block;
	}

	.left-panel::-webkit-scrollbar-track {
		background: transparent;
	}

	.left-panel::-webkit-scrollbar-thumb {
		background: #ccc;
		border-radius: 4px;
		transition: all 0.2s;
	}

	.left-panel::-webkit-scrollbar-thumb:hover {
		background: #555;
		width: 12px;
		border-radius: 6px;
	}

	.right-panel {
		width: 60%;
		position: relative;
	}

	.map {
		width: 100%;
		height: 100%;
	}

	.stats-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
	}

	.stats-header h2 {
		font-family: var(--font-title);
		font-size: 28px;
		margin: 0;
	}

	.filter-container {
		position: relative;
	}

	.filter-icon-button {
		width: 32px;
		height: 32px;
		border: none;
		background: transparent;
		cursor: pointer;
		color: #6b7280;
		border-radius: 6px;
		padding: 0;
	}

	.filter-icon-button:hover {
		background: #f3f4f6;
	}

	.filter-dropdown-menu {
		position: absolute;
		top: calc(100% + 4px);
		right: 0;
		background: white;
		border: 1px solid #e5e5e5;
		border-radius: 10px;
		box-shadow: 0 4px 20px rgba(0,0,0,0.12);
		padding: 6px;
		min-width: 180px;
		z-index: 1000;
	}

	.filter-option {
		width: 100%;
		padding: 10px 12px;
		border: none;
		background: transparent;
		text-align: left;
		font-size: 14px;
		cursor: pointer;
		border-radius: 6px;
	}

	.filter-option:hover {
		background: #f3f4f6;
	}

	.filter-option.active {
		background: #eff6ff;
		color: #007aff;
		font-weight: 500;
	}

	.left-panel p {
		color: #6b7280;
		margin: 0 0 16px;
	}

	.radius-control {
		margin: 16px 0;
	}

	.radius-control label {
		display: block;
		margin-bottom: 8px;
		font-size: 14px;
		color: #374151;
	}

	.radius-control input {
		width: 100%;
		cursor: pointer;
	}

	.street-list {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.highlighted {
		outline: 2px solid #4DB6ED;
		border-radius: 12px;
		animation: pulse 0.5s ease-in-out;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.02); }
	}

	.modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10000;
	}

	.modal-content {
		background: white;
		padding: 40px;
		border-radius: 16px;
		text-align: center;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
	}

	.spinner {
		width: 48px;
		height: 48px;
		border: 4px solid #e5e5e5;
		border-top: 4px solid #4DB6ED;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 16px;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.modal-content h3 {
		margin: 0 0 8px;
		font-size: 20px;
	}

	.modal-content p {
		margin: 0;
		color: #6b7280;
	}

	.checkmark {
		width: 64px;
		height: 64px;
		background: #10b981;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 40px;
		margin: 0 auto 16px;
	}

	.modal-content.success h3 {
		color: #10b981;
	}

	.cash-out-button {
		position: absolute;
		top: 16px;
		right: 16px;
		z-index: 1000;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 8px;
		padding: 12px 24px;
		font-family: var(--font-body);
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
	}

	.cash-out-button:hover:not(:disabled) {
		background: #059669;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
	}

	.cash-out-button:active:not(:disabled) {
		transform: translateY(0);
	}

	.cash-out-button:disabled {
		background: #d1d5db;
		cursor: not-allowed;
		box-shadow: none;
	}

	.modal-content.cash-out {
		min-width: 400px;
	}

	.modal-content.cash-out h3 {
		margin: 0 0 16px;
		font-size: 24px;
		color: #333;
	}

	.cash-out-amount {
		font-family: var(--font-title);
		font-size: 36px;
		color: #10b981;
		margin: 0 0 24px;
		font-weight: 600;
	}

	.cash-out-info {
		margin-bottom: 24px;
		text-align: left;
	}

	.cash-out-info label {
		display: block;
		margin-bottom: 8px;
		font-size: 14px;
		color: #374151;
		font-weight: 500;
	}

	.cash-out-info input {
		width: 100%;
		padding: 12px;
		border: 1px solid #d1d5db;
		border-radius: 8px;
		font-family: var(--font-body);
		font-size: 14px;
	}

	.cash-out-info input:focus {
		outline: none;
		border-color: #10b981;
		box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
	}

	.modal-buttons {
		display: flex;
		gap: 12px;
		justify-content: flex-end;
	}

	.cancel-button {
		padding: 10px 20px;
		background: transparent;
		border: 1px solid #d1d5db;
		border-radius: 8px;
		font-family: var(--font-body);
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.cancel-button:hover {
		background: #f3f4f6;
		border-color: #9ca3af;
	}

	.confirm-button {
		padding: 10px 20px;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 8px;
		font-family: var(--font-body);
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.confirm-button:hover {
		background: #059669;
	}

	/* Smooth transitions for map elements */
	:global(.radius-circle-animate) {
		transition: all 0.15s ease-in-out !important;
	}

	:global(.map-marker-animate) {
		transition: opacity 0.15s ease-in-out, transform 0.15s ease-out !important;
	}

	:global(.leaflet-interactive) {
		transition: opacity 0.15s ease-in-out !important;
	}
</style>
