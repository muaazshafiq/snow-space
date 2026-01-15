<div class="container">
	<div class="snowflakes" aria-hidden="true">
		{#each Array(40) as _, i}
			<div class="snowflake" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 15}s; animation-duration: {6 + Math.random() * 10}s; font-size: {1 + Math.random() * 1.5}em;">
				❄
			</div>
		{/each}
	</div>

	<div class="verify-section">
		<h1 class="title">Verify Your Identity</h1>
		<p class="subtitle">Upload a government-issued ID to get started</p>

		<div class="upload-box">
			<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
				<polyline points="17 8 12 3 7 8"></polyline>
				<line x1="12" y1="3" x2="12" y2="15"></line>
			</svg>
			<h3>Upload ID</h3>
			<p>Driver's license, passport, or government ID</p>
			<button class="upload-button">Choose File</button>
		</div>

		<div class="requirements">
			<h4>Requirements:</h4>
			<ul>
				<li>Photo must be clear and readable</li>
				<li>All corners of ID must be visible</li>
				<li>Accepted formats: JPG, PNG, PDF</li>
			</ul>
		</div>

		<a href="/home" class="skip-link">Skip for now</a>
	</div>
</div>

<style>
	.container {
		position: relative;
		min-height: 100vh;
		background: linear-gradient(to bottom, #ffffff 0%, #ffffff 30%, #4DB6ED 100%);
	}

	.snowflakes {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
		overflow: hidden;
	}

	.snowflake {
		position: absolute;
		top: -10%;
		color: #fff;
		opacity: 0.9;
		animation: fall linear infinite;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.8), 0 0 20px rgba(77, 182, 237, 0.4);
		filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.5));
	}

	@keyframes fall {
		0% {
			top: -10%;
			transform: translateX(0px) rotate(0deg);
			opacity: 0;
		}
		10% {
			opacity: 0.9;
		}
		90% {
			opacity: 0.9;
		}
		100% {
			top: 110%;
			transform: translateX(50px) rotate(360deg);
			opacity: 0;
		}
	}

	.verify-section {
		position: relative;
		z-index: 2;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		text-align: center;
		padding: 40px 20px;
		max-width: 600px;
		margin: 0 auto;
	}

	.title {
		font-family: var(--font-title);
		font-size: 40px;
		font-weight: normal;
		margin: 0 0 8px;
		color: #333;
	}

	.subtitle {
		font-family: var(--font-body);
		font-size: 16px;
		color: #666;
		margin: 0 0 40px;
	}

	.upload-box {
		background: white;
		border: 2px dashed #d1d5db;
		border-radius: 16px;
		padding: 48px 32px;
		width: 100%;
		max-width: 400px;
		transition: all 0.2s ease;
	}

	.upload-box:hover {
		border-color: #4DB6ED;
		box-shadow: 0 4px 12px rgba(77, 182, 237, 0.1);
	}

	.upload-box svg {
		color: #9ca3af;
		margin-bottom: 16px;
	}

	.upload-box h3 {
		font-family: var(--font-body);
		font-size: 20px;
		font-weight: 600;
		margin: 0 0 8px;
		color: #333;
	}

	.upload-box p {
		font-family: var(--font-body);
		font-size: 14px;
		color: #666;
		margin: 0 0 24px;
	}

	.upload-button {
		padding: 12px 32px;
		background: #4DB6ED;
		color: white;
		border: none;
		border-radius: 8px;
		font-family: var(--font-body);
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.upload-button:hover {
		background: #3da3d9;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(77, 182, 237, 0.3);
	}

	.upload-button:active {
		transform: translateY(0);
	}

	.requirements {
		margin-top: 32px;
		text-align: left;
		background: rgba(255, 255, 255, 0.8);
		padding: 20px 24px;
		border-radius: 12px;
		max-width: 400px;
		width: 100%;
	}

	.requirements h4 {
		font-family: var(--font-body);
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 12px;
		color: #333;
	}

	.requirements ul {
		margin: 0;
		padding-left: 20px;
	}

	.requirements li {
		font-family: var(--font-body);
		font-size: 13px;
		color: #666;
		margin-bottom: 6px;
		line-height: 1.5;
	}

	.skip-link {
		margin-top: 24px;
		padding: 8px 16px;
		font-family: var(--font-body);
		font-size: 14px;
		color: #666;
		text-decoration: underline;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.skip-link:hover {
		color: #333;
	}
</style>
