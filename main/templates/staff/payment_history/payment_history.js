axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({
    delimiters: ['[[', ']]'],
   
    data(){return{
        baseURL:'{{request.get_full_path}}',                                                                                                                 
              
        searchButtonText:'Search <i class="fas fa-search"></i>',

        //api
        errorMessage:"",
        history:[],
        startDate:"{{d_one_day}}",
        endDate:"{{d_today}}",

        //recruiter
        errorMessageRecruiter:"",
        historyRecruiter:[],
        startDateRecruiter:"{{d_one_month}}",
        endDateRecruiter:"{{d_today}}",

        //budget
        errorMessageBudget:"",
        historyBudget:[],
        startDateBudget:"{{d_fisical_start}}",
        endDateBudget:"{{d_today}}",

        expenditure_report:{department : "",
                            budget : ""},

        working : false,
    }},

    methods:{
        //get history of payments made to paypal api
        getHistory: function getHistory(){

            app.working = true;

            axios.post('{{request.get_full_path}}', {                            
                action: "getHistory",
                startDate: app.startDate,
                endDate: app.endDate,
                            
            })
            .then(function (response) {                         
                app.history = response.data.history;
                app.errorMessage = response.data.errorMessage;
                app.searchButtonText = 'Search <i class="fas fa-search"></i>';
                app.working = false;
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        }, 

        getHistoryButton : function getHistoryButton(){
            app.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            this.getHistory();
        },

        //get history of payments from recruiter
        getHistoryRecruiter: function getHistoryRecruiter(){
            app.working = true;
            app.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action: "getHistoryRecruiter",
                startDate: app.startDateRecruiter,
                endDate: app.endDateRecruiter,
                            
            })
            .then(function (response) {                         
                app.historyRecruiter = response.data.history;
                app.errorMessageRecruiter = response.data.errorMessage;
                app.searchButtonText = 'Search <i class="fas fa-search"></i>';
                app.working = false;
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },

        //get budget expenditures
        getHistoryBudget: function getHistoryBudget(){
            app.working = true;
            app.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action: "getHistoryBudget",
                startDate: app.startDateBudget,
                endDate: app.endDateBudget,
                expenditure_report : app.expenditure_report,
                            
            })
            .then(function (response) {                         
                app.historyBudget = response.data.history;
                app.historyBudgetCSV = response.data.history_csv;
                app.errorMessageBudget = response.data.errorMessage;
                app.searchButtonText = 'Search <i class="fas fa-search"></i>';
                app.working = false;
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },

        //get budget expenditures
        downloadHistoryBudget: function downloadHistoryBudget(){
            app.working = true;         
            
            app.working = false;

            var downloadLink = document.createElement("a");
            var blob = new Blob(["\ufeff", app.historyBudgetCSV]);
            var url = URL.createObjectURL(blob);
            downloadLink.href = url;
            downloadLink.download = "Budget_Report_" + app.startDateBudget + "_to_"+ app.endDateBudget + ".csv";

            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        },
      
    },
    
    mounted(){
        //this.getHistory();
    },
}).mount('#app');