<script>
	let { children, peekContent, isPeekMode = $bindable(false) } = $props();

	// Snap points (now in pixels/percentage for better control)
	const PEEK_HEIGHT_PX = 120; // Minimized state in pixels - shows handle + stats
	const EXPANDED_HEIGHT_PERCENT = 77; // Full view - percentage of screen (reduced by 15% to avoid radius slider overlap)

	let drawerHeight = $state(EXPANDED_HEIGHT_PERCENT);
	let startY = $state(0);
	let startHeight = $state(0);
	let isDragging = $state(false);
	let isTransitioning = $state(false);
	let containerElement = $state(null);

	// For velocity tracking
	let lastY = $state(0);
	let lastTime = $state(0);
	let velocity = $state(0);

	function handleDragStart(e) {
		e.preventDefault();
		isDragging = true;
		isTransitioning = false;

		const clientY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY;
		startY = clientY;
		lastY = clientY;
		lastTime = Date.now();
		startHeight = drawerHeight;
		velocity = 0;
	}

	function handleDragMove(e) {
		if (!isDragging) return;

		const currentY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY;
		const currentTime = Date.now();

		// Calculate velocity for snap prediction
		const timeDelta = currentTime - lastTime;
		if (timeDelta > 0) {
			const yDelta = currentY - lastY;
			velocity = yDelta / timeDelta; // pixels per millisecond
		}

		lastY = currentY;
		lastTime = currentTime;

		// Calculate new height using actual container height
		const deltaY = startY - currentY;
		const containerHeight = containerElement?.clientHeight || window.innerHeight;
		const deltaPercent = (deltaY / containerHeight) * 100;

		// Calculate peek height as percentage
		const peekHeightPercent = (PEEK_HEIGHT_PX / containerHeight) * 100;

		// Apply elastic resistance at boundaries
		let newHeight = startHeight + deltaPercent;

		// Add resistance when dragging beyond bounds
		if (newHeight > EXPANDED_HEIGHT_PERCENT) {
			const excess = newHeight - EXPANDED_HEIGHT_PERCENT;
			newHeight = EXPANDED_HEIGHT_PERCENT + (excess * 0.3); // 70% resistance
		} else if (newHeight < peekHeightPercent) {
			const deficit = peekHeightPercent - newHeight;
			newHeight = peekHeightPercent - (deficit * 0.3); // 70% resistance
		}

		drawerHeight = newHeight;
		isPeekMode = newHeight < 40;
	}

	function handleDragEnd() {
		if (!isDragging) return;
		isDragging = false;
		isTransitioning = true;

		// Calculate peek height as percentage using actual container height
		const containerHeight = containerElement?.clientHeight || window.innerHeight;
		const peekHeightPercent = (PEEK_HEIGHT_PX / containerHeight) * 100;

		// Determine snap target based on velocity and position
		let targetHeight;

		// Strong velocity triggers immediate snap
		const VELOCITY_THRESHOLD = 0.3; // pixels per millisecond
		const SNAP_THRESHOLD = 50; // Midpoint percentage

		if (velocity > VELOCITY_THRESHOLD) {
			// Swiping up fast -> expand
			targetHeight = EXPANDED_HEIGHT_PERCENT;
		} else if (velocity < -VELOCITY_THRESHOLD) {
			// Swiping down fast -> minimize
			targetHeight = peekHeightPercent;
		} else {
			// Use position-based snapping
			targetHeight = drawerHeight > SNAP_THRESHOLD ? EXPANDED_HEIGHT_PERCENT : peekHeightPercent;
		}

		drawerHeight = targetHeight;
		isPeekMode = targetHeight < 40;

		// Reset transition flag after animation completes
		setTimeout(() => {
			isTransitioning = false;
		}, 300);
	}

	function handleBackdropClick(e) {
		const containerHeight = containerElement?.clientHeight || window.innerHeight;
		const peekHeightPercent = (PEEK_HEIGHT_PX / containerHeight) * 100;

		if (e.target === e.currentTarget && !isPeekMode) {
			isTransitioning = true;
			drawerHeight = peekHeightPercent;
			isPeekMode = true;
			setTimeout(() => {
				isTransitioning = false;
			}, 300);
		}
	}

	function handlePeekClick() {
		if (isPeekMode) {
			isTransitioning = true;
			drawerHeight = EXPANDED_HEIGHT_PERCENT;
			isPeekMode = false;
			setTimeout(() => {
				isTransitioning = false;
			}, 300);
		}
	}

	function handlePeekKeydown(e) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			handlePeekClick();
		}
	}

	// Initialize peek mode state (only in browser)
	$effect(() => {
		if (typeof window !== 'undefined' && containerElement) {
			const containerHeight = containerElement.clientHeight || window.innerHeight;
			const peekHeightPercent = (PEEK_HEIGHT_PX / containerHeight) * 100;
			isPeekMode = drawerHeight <= peekHeightPercent + 5; // 5% buffer
		}
	});
</script>

<div
	bind:this={containerElement}
	class="drawer-backdrop"
	onclick={handleBackdropClick}
	role="presentation"
	class:peek-mode={isPeekMode}
	style="background-color: rgba(0, 0, 0, {isPeekMode ? 0 : Math.min(0.5, (drawerHeight / 100) * 0.5)});"
>
	<div
		class="drawer-content"
		class:transitioning={isTransitioning}
		class:dragging={isDragging}
		style="height: {drawerHeight}%"
	>
		<div
			class="drawer-handle-area"
			onmousedown={handleDragStart}
			ontouchstart={handleDragStart}
			role="button"
			tabindex="0"
		>
			<div class="drawer-handle"></div>
		</div>

		{#if isPeekMode}
			<!-- Peek state content -->
			<div class="drawer-peek" onclick={handlePeekClick} onkeydown={handlePeekKeydown} role="button" tabindex="0">
				{#if peekContent}
					{@render peekContent()}
				{:else}
					<div class="default-peek">
						<p class="peek-label">Tap to expand</p>
					</div>
				{/if}
			</div>
		{:else}
			<!-- Expanded state content -->
			<div class="drawer-body">
				{@render children()}
			</div>
		{/if}
	</div>
</div>

<svelte:window
	onmousemove={handleDragMove}
	onmouseup={handleDragEnd}
	ontouchmove={handleDragMove}
	ontouchend={handleDragEnd}
/>

<style>
	.drawer-backdrop {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 50;
		display: flex;
		align-items: flex-end;
		justify-content: center;
		transition: background-color 0.3s ease;
		pointer-events: none; /* Allow clicks through when minimized */
	}

	.drawer-backdrop.peek-mode {
		pointer-events: none; /* Backdrop doesn't block in peek mode */
	}

	.drawer-backdrop:not(.peek-mode) {
		pointer-events: auto; /* Backdrop blocks clicks when expanded */
	}

	.drawer-content {
		background-color: white;
		border-radius: 24px 24px 0 0;
		width: 100%;
		min-height: 120px; /* Ensure drawer is always visible */
		box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
		display: flex;
		flex-direction: column;
		position: relative;
		pointer-events: auto; /* Always allow interaction with drawer */
	}

	.drawer-content.dragging {
		transition: none;
	}

	.drawer-content.transitioning {
		transition: height 0.3s cubic-bezier(0.32, 0.72, 0, 1);
	}

	.drawer-handle-area {
		padding: var(--spacing-sm) var(--spacing-md);
		cursor: grab;
		display: flex;
		justify-content: center;
		align-items: center;
		flex-shrink: 0;
		touch-action: none;
		-webkit-user-select: none;
		user-select: none;
		min-height: 48px;
	}

	.drawer-handle-area:active {
		cursor: grabbing;
	}

	.drawer-handle {
		width: 48px;
		height: 4px;
		background-color: #d1d5db;
		border-radius: 2px;
		transition: background-color 0.2s;
	}

	.drawer-handle-area:hover .drawer-handle {
		background-color: #9ca3af;
	}

	.drawer-body {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
		-webkit-overflow-scrolling: touch;
	}

	.drawer-peek {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: var(--spacing-xs) var(--spacing-md) var(--spacing-md);
		overflow: hidden;
		cursor: pointer;
		-webkit-user-select: none;
		user-select: none;
		min-height: 0;
	}

	.drawer-peek:active {
		opacity: 0.8;
	}

	.default-peek {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
	}

	.peek-label {
		font-family: var(--font-body);
		font-size: 14px;
		color: #9ca3af;
		margin: 0;
	}

	/* Prevent body scroll when drawer is expanded */
	:global(body:has(.drawer-content)) {
		overflow: hidden;
	}
</style>
