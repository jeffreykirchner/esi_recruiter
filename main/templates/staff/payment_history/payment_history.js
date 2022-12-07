axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({
    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{
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
    },

    methods:{
        //get history of payments made to paypal api
        getHistory: function(){

            app.$data.working = true;

            axios.post('{{request.get_full_path}}', {                            
                action: "getHistory",
                startDate: app.$data.startDate,
                endDate: app.$data.endDate,
                            
            })
            .then(function (response) {                         
                app.$data.history = response.data.history;
                app.$data.errorMessage = response.data.errorMessage;
                app.$data.searchButtonText = 'Search <i class="fas fa-search"></i>';
                app.$data.working = false;
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        }, 

        getHistoryButton : function(){
            app.$data.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            this.getHistory();
        },

        //get history of payments from recruiter
        getHistoryRecruiter: function(){
            app.$data.working = true;
            app.$data.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action: "getHistoryRecruiter",
                startDate: app.$data.startDateRecruiter,
                endDate: app.$data.endDateRecruiter,
                            
            })
            .then(function (response) {                         
                app.$data.historyRecruiter = response.data.history;
                app.$data.errorMessageRecruiter = response.data.errorMessage;
                app.$data.searchButtonText = 'Search <i class="fas fa-search"></i>';
                app.$data.working = false;
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },

        //get budget expenditures
        getHistoryBudget: function(){
            app.$data.working = true;
            app.$data.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action: "getHistoryBudget",
                startDate: app.$data.startDateBudget,
                endDate: app.$data.endDateBudget,
                expenditure_report : app.$data.expenditure_report,
                            
            })
            .then(function (response) {                         
                app.$data.historyBudget = response.data.history;
                app.$data.errorMessageBudget = response.data.errorMessage;
                app.$data.searchButtonText = 'Search <i class="fas fa-search"></i>';
                app.$data.working = false;
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },

        //get budget expenditures
        downloadHistoryBudget: function(){
            app.$data.working = true;         
            
            app.$data.working = false;

            let data = "Budget,Account Name,Account Number,Department,Session,Payments";

            //for(let i=0;)

            var downloadLink = document.createElement("a");
            var blob = new Blob(["\ufeff", data]);
            var url = URL.createObjectURL(blob);
            downloadLink.href = url;
            downloadLink.download = "Budget_Report_" + app.$data.startDateBudget + "_to_"+ app.$data.endDateBudget + ".csv";

            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);

             
        },
      
    },
    
    mounted: function(){
        //this.getHistory();
    },
});