// The function accepts a single argument: the "context" object.
// For a complete list of its properties and functions,
// see https://apify.com/apify/web-scraper#page-function 
async function pageFunction(context) {
    // This statement works as a breakpoint when you're trying to debug your code. Works only with Run mode: DEVELOPMENT!
    // debugger; 

    // jQuery is handy for finding DOM elements and extracting data from them.
    // To use it, make sure to enable the "Inject jQuery" option.
    const $ = context.jQuery;
    const pageTitle = $('title').first().text();
    const companyName = $("div.sc-bcXHqe.NcSfA.spec-profile-name-with-tooltip strong a.daisy-link.routerlink").text();
    const dateRegex = /Reported (.*?)[+-]/

    const bountyAmount = $("span.spec-amount-in-currency").text(); 
    const severityRating = $("span.spec-severity-rating").text();
    const severityScore = $("span.spec-severity-score").text().trim();
    const cleanSeverityScore = severityScore.replace('(', '').replace(')', '')
    const weakness = $("div.spec-weakness-meta-item").text().trim();
    const cleanWeakness = weakness.replace('Weakness', ''); 
    const title = $("div.spec-report-title").text();
    const reportDate = $("div.daisy-helper-text").text().match(dateRegex);
    const timeline = $("div.spec-report-timeline").text();
    const researcherSummary = $("div.spec-researcher-summary").text();
    const reportDescription = (timeline + researcherSummary).trim()
        
    if (context.request.url.startsWith("https://hackerone.com")) {
        // Print some information to actor log
        context.log.info(`URL: ${context.request.url}, 
            COMPANY: ${companyName},
            TITLE: ${title},
            REPORT DATE: ${reportDate[1].trim()},
            SEVERITY RATING: ${severityRating},
            SEVERITY SCORE: ${cleanSeverityScore},
            WEAKNESS: ${cleanWeakness},
            BOUNTY AMOUNT: ${bountyAmount},
            DESCRIPTION: ${reportDescription}
            `);


        // Manually add a new page to the queue for scraping.
        // await context.enqueueRequest({ url: 'http://www.example.com' });

        // Return an object with the data extracted from the page.
        // It will be stored to the resulting dataset.
        return {
            companyName: companyName,
            reportDate: reportDate[1].trim(),
            weakness: cleanWeakness,
            severityRating: severityRating,
            severityScore: cleanSeverityScore,
            bountyAwarded: bountyAmount,
            title: title,
            reportDescription: reportDescription,
            url: context.request.url
        };
    }
    else {
        return null
    }


}
