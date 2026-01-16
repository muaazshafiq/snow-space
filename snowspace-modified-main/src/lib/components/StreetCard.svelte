<script>
	let { coordinates, streetName, price, priorityScore, onComplete } = $props();

	let isCompleted = $state(false);

	function handleComplete() {
		isCompleted = !isCompleted;
		if (onComplete) {
			onComplete(price, isCompleted);
		}
	}

	// Calculate color based on priority score (0 = green, 10 = red)
	function getPriorityColor(score) {
		// Clamp score between 0 and 10
		const clampedScore = Math.max(0, Math.min(10, score));
		const ratio = clampedScore / 10;

		// Interpolate from green (10, 185, 129) to red (239, 68, 68)
		const r = Math.round(10 + ratio * (239 - 10));
		const g = Math.round(185 - ratio * (185 - 68));
		const b = Math.round(129 - ratio * (129 - 68));

		return `rgb(${r}, ${g}, ${b})`;
	}
</script>

<div class="street-card" class:completed={isCompleted}>
	<div class="price">${price}</div>
	<div class="street-info">
		<span class="street-name" title={`${coordinates.lat}, ${coordinates.lng}`}>
			{streetName}
		</span>
		<span class="priority-score">
			Priority: <span style="color: {getPriorityColor(priorityScore)}; font-weight: 600;">{priorityScore}</span>
		</span>
	</div>
	<button class="complete-button" onclick={handleComplete} aria-label="Mark as complete">
		{isCompleted ? '✓' : '○'}
	</button>
</div>

<style>
	.street-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm) var(--spacing-md);
		background: #ffffff;
		border: 1px solid var(--color-border);
		border-radius: 12px;
		transition: all 0.2s ease;
	}

	.street-card:hover {
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
		border-color: #d1d5db;
	}

	.street-card.completed {
		opacity: 0.6;
		background: #f9fafb;
	}

	.price {
		font-family: var(--font-title);
		font-size: 20px;
		font-weight: normal;
		color: #10b981;
		min-width: 80px;
		flex-shrink: 0;
	}

	.street-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
		min-width: 0;
	}

	.street-name {
		font-family: var(--font-body);
		font-size: 14px;
		font-weight: 500;
		color: var(--color-text);
		cursor: help;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.priority-score {
		font-family: var(--font-body);
		font-size: 12px;
		color: #6b7280;
	}

	.complete-button {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		border: 2px solid #d1d5db;
		background: white;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 16px;
		padding: 0;
		flex-shrink: 0;
	}

	.complete-button:hover {
		border-color: #10b981;
		background: #f0fdf4;
	}

	.street-card.completed .complete-button {
		border-color: #10b981;
		background: #10b981;
		color: white;
	}
</style>
