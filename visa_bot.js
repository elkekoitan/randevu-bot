```javascript
    import puppeteer from 'puppeteer';
    import { writeFile } from 'fs/promises';

    class VisaAppointmentBot {
      constructor() {
        this.baseUrl = 'https://ais.usvisa-info.com/tr-tr/niv/groups/46114340';
        this.appointmentUrl = 'https://ais.usvisa-info.com/tr-tr/niv/schedule/64807632/appointment';
        this.currentAppointmentDate = null;
        this.email = 'turhanhamza@gmail.com'; // Replace with your email
        this.password = '7234459Qwee.'; // Replace with your password
      }

      async takeScreenshot(page, name) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `screenshots/${name}_${timestamp}.png`;
        await page.screenshot({ path: filename });
        await this.log(`Screenshot saved: ${filename}`);
      }

      async log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `${timestamp} - ${message}\n`;
        console.log(logMessage);
        await writeFile('visa_bot.log', logMessage, { flag: 'a' });
      }

      async login(page) {
        await this.log('Logging in...');
        await page.goto('https://ais.usvisa-info.com/tr-tr/niv/users/sign_in');
        await page.waitForSelector('#user_email');
        await page.type('#user_email', this.email);
        await page.type('#user_password', this.password);
        await page.click('[name="policy_confirmed"]');
        await page.click('[name="commit"]');
        await this.log('Login successful!');
      }

      async getCurrentDate(page) {
        await this.log('Retrieving current appointment date...');
        await page.goto(this.baseUrl);
        const dateElement = await page.$('p.consular-appt strong');
        const dateTextNode = await page.evaluate(el => el.nextSibling.textContent.trim(), dateElement);
        let dateStr = dateTextNode.split(' Ankara')[0].trim();

        const trMonths = {
          'Ocak': 'January', 'Şubat': 'February', 'Mart': 'March',
          'Nisan': 'April', 'Mayıs': 'May', 'Haziran': 'June',
          'Temmuz': 'July', 'Ağustos': 'August', 'Eylül': 'September',
          'Ekim': 'October', 'Kasım': 'November', 'Aralık': 'December'
        };

        for (const [tr, eng] of Object.entries(trMonths)) {
          dateStr = dateStr.replace(tr, eng);
        }

        this.currentAppointmentDate = new Date(dateStr);
        await this.log(`Current appointment date: ${this.currentAppointmentDate.toDateString()}`);
      }

      async findEarlierDate(page) {
        await this.log('Checking for earlier appointment...');
        await page.goto(this.appointmentUrl);
        await page.waitForSelector('#appointments_consulate_appointment_facility_id');
        await page.select('#appointments_consulate_appointment_facility_id', '105');
        await page.click('#appointments_consulate_appointment_date');

        let monthsChecked = 0;
        while (monthsChecked < 24) {
          const activeDates = await page.$$('td.day:not(.disabled)');
          if (activeDates.length > 0) {
            const firstDate = activeDates[0];
            const dateStr = await page.evaluate(el => el.getAttribute('data-date'), firstDate);
            const availableDate = new Date(dateStr);

            if (availableDate < this.currentAppointmentDate) {
              await firstDate.click();
              await this.log('Earlier date found and selected');
              await page.waitForSelector('#appointments_consulate_appointment_time');
              await page.select('#appointments_consulate_appointment_time', '09:00');
              await page.click('[name="commit"]');
              await page.waitForSelector('.button.alert');
              await page.click('.button.alert');
              await this.log('New appointment successfully created!');
              return true;
            }
          }

          const nextMonthButton = await page.$('.ui-datepicker-next');
          const isDisabled = await page.evaluate(el => el.classList.contains('ui-state-disabled'), nextMonthButton);

          if (isDisabled) {
            await this.log('Reached the last available month');
            break;
          }

          await nextMonthButton.click();
          await new Promise(resolve => setTimeout(resolve, 1000));
          monthsChecked++;
        }

        await this.log('No earlier appointment found within the next two years.');
        return false;
      }

      async run() {
        const browser = await puppeteer.launch({ headless: false });
        const page = await browser.newPage();

        try {
          await this.login(page);
          await this.getCurrentDate(page);
          let attempt = 1;
          while (true) {
            await this.log(`Attempt ${attempt} starting...`);
            if (await this.findEarlierDate(page)) {
              await this.log('Success! An earlier appointment was found and scheduled.');
              break;
            }
            await this.log('Retrying in 3 minutes...');
            await new Promise(resolve => setTimeout(resolve, 180000));
            attempt++;
          }
        } catch (error) {
          await this.log(`Critical error: ${error.message}`);
          await this.takeScreenshot(page, 'critical_error');
        } finally {
          await browser.close();
        }
      }
    }

    const bot = new VisaAppointmentBot();
    bot.run();
    ```
