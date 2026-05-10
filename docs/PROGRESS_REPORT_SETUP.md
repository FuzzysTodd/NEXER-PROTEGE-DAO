# Automated Progress Report Email Workflow Setup

This document outlines the setup instructions for the automated progress report email workflow that sends Gantt charts twice daily to fuzzystodd@gmail.com.

## 1. Gmail App Password Setup
To use Gmail for sending emails, you need to set up an App Password:
1. Sign in to your Google Account.
2. Navigate to `Security` > `Signing in to Google`.
3. Enable `2-Step Verification` if not already enabled.
4. Go to `App passwords`.
5. Create a new app password specific for this workflow and save it.

## 2. GitHub Secrets Configuration
Store your Gmail credentials in GitHub secrets:
1. Go to your repository on GitHub.
2. Click on `Settings` > `Secrets and variables` > `Actions` > `New repository secret`.
3. Add `EMAIL_USERNAME` with your Gmail address.
4. Add `EMAIL_PASSWORD` with the app password you generated in the previous step.

## 3. Workflow Enablement Steps
1. Ensure the workflow YAML file is located in `.github/workflows/` within your repository.
2. Check if the GitHub Actions are enabled in your repository settings.
3. Push the changes to the main branch to trigger the initial run of the workflow.

## 4. Manual Testing Instructions
To manually test the email sending functionality:
1. Trigger the workflow from the GitHub Actions tab.
2. Check your email for the Gantt chart report.
3. Verify the email format and contents.

## 5. Report Contents Description
The report will contain:
- Latest Gantt charts.
- Project progress updates.
- Any critical tasks or alerts.

## 6. Schedule Details
The workflow is scheduled to run:
- **9 AM UTC**
- **9 PM UTC**

Ensure that your workflow configuration includes triggers for the above schedules.

## 7. Customization Options
You can customize:
- Email contents by modifying the template within the workflow file.
- The schedule by changing cron jobs in the workflow YAML file.

## 8. Security Notes
- Never hardcode sensitive information directly in the workflow file.
- Regularly review and update the app passwords and GitHub secrets.

## 9. Verification Steps
- Verify the app password by sending a test email.
- Check the logs of the GitHub Actions run for errors or warnings.

## 10. Troubleshooting Guidance
If you encounter issues:
- Ensure that the workflow file is correctly configured.
- Double-check GitHub secrets for proper configuration.
- Review the workflow logs to identify potential errors.

By following these instructions, you will set up a fully functional automated progress report email workflow that efficiently sends Gantt charts twice a day.