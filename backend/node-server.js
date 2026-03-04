import express from 'express';
import cors from 'cors';
import nodemailer from 'nodemailer';
import { config as loadEnv } from 'dotenv';

loadEnv(); // Loads environment variables from .env if present

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 5000;

app.use(cors({ origin: true, credentials: false }));
app.use(express.json({ limit: '1mb' }));

function buildWelcomeEmail({ email, name }) {
	// Fallback to a friendly greeting if name is not provided
	const firstName = (name || '').trim().split(' ')[0] || 'there';
	const subject = 'Welcome to TEI-HA AI Tools';
	const text = [
		`Hi ${firstName},`,
		'',
		'Welcome to TEI-HA Construction Services AI Tools!',
		'We are excited to have you on board. You can now explore our AI-powered features to sketch, estimate budgets, craft styles, and scout sites to accelerate your project.',
		'',
		'Getting started:',
		'- Open the site and try any of the AI tools from the features section',
		'- You can return any time and continue where you left off',
		'',
		'Disclaimer: The AI outputs are indicative and not a final say. Please contact TEI-HA Construction Services Ltd to draw final professional conclusions.',
		'',
		'If you have any questions, just reply to this email.',
		'',
		'Best regards,',
		'TEI-HA Construction Services Ltd'
	].join('\n');
	const html = `
<!doctype html>
<html>
<body style="font-family: Arial, sans-serif; color: #111827; line-height: 1.5; padding: 16px;">
	<div style="max-width:600px;margin:0 auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
		<div style="background:#1173d4;color:#fff;padding:16px 20px;">
			<h1 style="margin:0;font-size:20px;">Welcome to TEI-HA AI Tools</h1>
		</div>
		<div style="padding:20px;background:#ffffff;">
			<p>Hi ${firstName},</p>
			<p>Welcome to <strong>TEI-HA Construction Services AI Tools</strong>!</p>
			<p>We are excited to have you on board. You can now explore our AI-powered features to sketch, estimate budgets, craft styles, and scout sites to accelerate your project.</p>
			<p style="margin:16px 0 8px 0;"><strong>Getting started</strong></p>
			<ul style="margin:0 0 16px 20px;">
				<li>Open the site and try any of the AI tools from the features section</li>
				<li>You can return any time and continue where you left off</li>
			</ul>
			<p style="margin:0 0 8px 0;"><strong>Disclaimer</strong></p>
			<p style="margin:0 0 16px 0;">The AI outputs are indicative and not a final say. Please contact TEI-HA Construction Services Ltd to draw final professional conclusions.</p>
			<p>If you have any questions, just reply to this email.</p>
			<p style="margin-top:24px;">Best regards,<br/>TEI-HA Construction Services Ltd</p>
		</div>
	</div>
</body>
</html>
`.trim();
	return { subject, text, html };
}

async function createTransporter() {
	const host = process.env.SMTP_HOST || '';
	const port = process.env.SMTP_PORT ? parseInt(process.env.SMTP_PORT, 10) : 587;
	const user = process.env.SMTP_USER || '';
	const pass = process.env.SMTP_PASS || '';
	const hasCreds = host && user && pass;
	if (!hasCreds) {
		console.warn('SMTP credentials not configured. Emails will be logged instead of sent.');
		return null;
	}
	return nodemailer.createTransport({
		host,
		port,
		secure: port === 465,
		auth: { user, pass }
	});
}

app.get('/health', (_req, res) => {
	res.json({ status: 'ok', service: 'teiha-backend-js' });
});

// Minimal in-memory set to avoid duplicate sends in quick succession
const recentRegistrations = new Set();
setInterval(() => recentRegistrations.clear(), 1000 * 60 * 10); // clear every 10 mins

app.post('/api/users/register', async (req, res) => {
	try {
		const email = (req.body?.email || '').trim().toLowerCase();
		const name = (req.body?.name || '').trim();
		const phone = (req.body?.phone || '').trim();
		if (!email || !email.includes('@')) {
			return res.status(400).json({ error: 'Invalid email' });
		}

		// Throttle duplicate email events briefly
		if (recentRegistrations.has(email)) {
			return res.json({ status: 'ok', duplicate: true });
		}
		recentRegistrations.add(email);

		const { subject, text, html } = buildWelcomeEmail({ email, name });
		const transporter = await createTransporter();
		const from = process.env.FROM_EMAIL || 'TEI-HA Construction <no-reply@teiha.local>';

		if (transporter) {
			await transporter.sendMail({
				from,
				to: email,
				subject,
				text,
				html
			});
		} else {
			console.log('--- Simulated email send (no SMTP configured) ---');
			console.log('To:', email);
			console.log('Subject:', subject);
			console.log('Text:\n', text);
		}

		// Optional: notify admin
		const adminEmail = process.env.ADMIN_EMAIL || '';
		if (transporter && adminEmail) {
			await transporter.sendMail({
				from,
				to: adminEmail,
				subject: 'New AI tools signup',
				text: `User registered: ${email}${name ? ` (${name})` : ''}${phone ? `, phone: ${phone}` : ''}`
			});
		}

		return res.json({ status: 'ok' });
	} catch (err) {
		console.error('Error in /api/users/register:', err);
		return res.status(500).json({ error: 'Internal server error' });
	}
});

app.listen(PORT, () => {
	console.log(`TEI-HA JS backend listening on http://localhost:${PORT}`);
});

