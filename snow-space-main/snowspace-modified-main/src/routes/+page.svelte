<div class="container">
	<div class="snowflakes" aria-hidden="true">
		{#each Array(60) as _, i}
			<div class="snowflake" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 15}s; animation-duration: {6 + Math.random() * 10}s; font-size: {1 + Math.random() * 1.5}em;">
				❄
			</div>
		{/each}
	</div>

	<div class="auth-section">
		<h1 class="title">SnowSpace</h1>
		<p class="tagline">Clear the snow, watch your earnings grow</p>

		<img src="/icons/snowspace-logo-lm.svg" alt="SnowSpace Logo" class="logo" />

		<div class="features">
			<div class="feature">
				<div class="feature-icon">
					<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="12" y1="1" x2="12" y2="23"></line>
						<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
					</svg>
				</div>
				<h3>Earn More</h3>
				<p>Get paid for every street you clear</p>
			</div>
			<div class="feature">
				<div class="feature-icon">
					<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
						<circle cx="12" cy="10" r="3"></circle>
					</svg>
				</div>
				<h3>Work Local</h3>
				<p>Find jobs near you instantly</p>
			</div>
			<div class="feature">
				<div class="feature-icon">
					<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
					</svg>
				</div>
				<h3>Flexible Hours</h3>
				<p>Choose when and where you work</p>
			</div>
		</div>

		<div class="divider">
			<span class="line"></span>
			<span class="divider-text">CONTINUE WITH</span>
			<span class="line"></span>
		</div>

		<div class="auth-buttons">
			<button class="auth-button" aria-label="Continue with Google">
				<img src="/icons/google-auth-icon.svg" alt="Google" />
			</button>
			<button class="auth-button" aria-label="Continue with Apple">
				<img src="/icons/apple-auth-icon.svg" alt="Apple" />
			</button>
			<button class="auth-button" aria-label="Continue with Phone">
				<img src="/icons/phone-auth-icon.svg" alt="Phone" />
			</button>
		</div>

		<a href="/verify" class="skip-button">Skip</a>
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

	.auth-section {
		position: relative;
		z-index: 2;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		gap: 0;
		text-align: center;
		padding-bottom: 20vh;
	}

	.title {
		font-family: var(--font-title);
		font-size: 48px;
		font-weight: normal;
		margin: 0;
		color: #4DB6ED;
		margin-bottom: 4px;
	}

	.tagline {
		font-family: var(--font-subtitle);
		font-style: italic;
		font-size: 18px;
		color: #666;
		margin: 0;
		margin-bottom: 16px;
	}

	.logo {
		width: 200px;
		height: 200px;
		margin: 0;
	}

	.features {
		display: flex;
		gap: 32px;
		margin: 32px 0;
		max-width: 700px;
	}

	.feature {
		flex: 1;
		text-align: center;
	}

	.feature-icon {
		margin-bottom: 12px;
		color: #4DB6ED;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.feature h3 {
		font-family: var(--font-body);
		font-size: 16px;
		font-weight: 600;
		margin: 0 0 4px;
		color: #333;
	}

	.feature p {
		font-family: var(--font-body);
		font-size: 13px;
		margin: 0;
		color: #666;
		line-height: 1.4;
	}

	.divider {
		display: flex;
		align-items: center;
		width: 100%;
		max-width: 320px;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-sm);
	}

	.line {
		flex: 1;
		height: 1px;
		background-color: var(--color-border);
	}

	.divider-text {
		font-family: var(--font-body);
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.5px;
		color: #999;
	}

	.auth-buttons {
		display: flex;
		gap: var(--spacing-md);
		margin-top: var(--spacing-sm);
	}

	.auth-button {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		border: 1.5px solid var(--color-border);
		background-color: #ffffff;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.2s ease;
		padding: 0;
	}

	.auth-button:hover {
		transform: scale(1.05);
		border-color: #ccc;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
	}

	.auth-button:active {
		transform: scale(0.98);
	}

	.auth-button img {
		width: 32px;
		height: 32px;
		object-fit: contain;
	}

	.skip-button {
		margin-top: var(--spacing-lg);
		padding: 12px 48px;
		background-color: transparent;
		border: 1.5px solid var(--color-border);
		border-radius: 24px;
		font-family: var(--font-subtitle);
		font-style: italic;
		font-size: 16px;
		color: #666;
		text-decoration: none;
		cursor: pointer;
		transition: all 0.2s ease;
		display: inline-block;
	}

	.skip-button:hover {
		border-color: #999;
		color: #333;
		background-color: rgba(0, 0, 0, 0.02);
	}

	.skip-button:active {
		transform: scale(0.98);
	}
</style>
