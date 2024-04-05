axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],
       
    data(){return{
        searchInfo:"",
        experiments:[],
        experiments_recent:[],
        searchCount:0,
        searchButtonText:'Search <i class="fas fa-search"></i>',
        warningText:"",
        showAllButtonText : 'Show All',
        showOpenButtonText : 'Show Open',
        createExperimentButtonText : 'Create Experiment <i class="fas fa-plus"></i>',
        dateSortButtonText: 'Date <i class="fas fa-sort"></i>',
        titleSortButtonText: 'Title <i class="fas fa-sort"></i>',
        managerSortButtonText: 'Manager <i class="fas fa-sort"></i>',

    }},

    methods:{
        //sort experiments by date
        sortByDate:function(){

            app.$data.dateSortButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            app.$data.experiments.sort(function(a, b) {
                if(b.date_start == "No Sessions")
                {
                    return 1; 
                }
                else if( a.date_start == "No Sessions")
                {
                    return -1;
                }
                else
                {
                    return new  Date(b.date_start) - new Date(a.date_start);
                }

            });

            app.$data.dateSortButtonText = 'Date <i class="fas fa-sort"></i>';
        },

        //sort by title
        sortByTitle:function(){

            app.$data.titleSortButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            app.$data.experiments.sort(function(a, b) {
                a=a.title.trim().toLowerCase();
                b=b.title.trim().toLowerCase();
                return a < b ? -1 : a > b ? 1 : 0;
            });

            app.$data.titleSortButtonText = 'Title <i class="fas fa-sort"></i>';
        },

        //sort by manager
        sortByManager:function(){

            app.$data.managerSortButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            app.$data.experiments.sort(function(a, b) {
                a=a.experiment_manager.trim().toLowerCase();
                b=b.experiment_manager.trim().toLowerCase();
                return a < b ? -1 : a > b ? 1 : 0;
            });

            app.$data.managerSortButtonText = 'Manager <i class="fas fa-sort"></i>';
            },

        //get list of experiments based on search
        searchExperiments:function(){
            if(app.$data.searchInfo == "")
                return;

            app.$data.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.$data.experiments=[];
            app.$data.warningText = "";

            axios.post('/experimentSearch/', {
                            action :"searchExperiments" ,
                            searchInfo:app.$data.searchInfo,                                                                                                                             
                        })
                        .then(function (response) {     
                            app.updateExperiments(response);
                            app.$data.searchButtonText = 'Search <i class="fas fa-search"></i>';                                                   
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.$data.searching=false;
                        });                        
        },
        
        //create new experient
        createExperiment:function(){                    
            app.$data.experiments = [];
            app.$data.warningText = '';
            app.$data.createExperimentButtonText ='<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experimentSearch/', {
                            action :"createExperiment" ,                                                                                                                                                                
                        })
                        .then(function (response) {     
                            app.updateExperiments(response);        
                            app.$data.createExperimentButtonText = 'Create Experiment <i class="fas fa-plus"></i>';                                        
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.$data.searching=false;
                        });                        
        },
        
        //get list of all experiments
        getAllExperiments:function(){
            app.$data.showAllButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.$data.experiments = [];
            app.$data.warningText = "";

            axios.post('/experimentSearch/', {
                            action :"getAllExperiments" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.updateExperiments(response);
                            app.$data.showAllButtonText = 'Show All';
                           
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.$data.searching=false;
                        });                        
                    },
        
        //get list of open experiments
        getOpenExperiments:function(){
            app.$data.showOpenButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.$data.experiments = [];
            app.$data.warningText = "";

            axios.post('/experimentSearch/', {
                            action :"getOpenExperiments" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.updateExperiments(response);
                            app.$data.showOpenButtonText = 'Show Open';
                           
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.$data.searching=false;
                        });                        
                    },
        
        //get recent experiments
        getRecentExperiments:function(){
            
            axios.post('/experimentSearch/', {
                            action :"getRecentExperiments" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.$data.experiments_recent = response.data.experiments_recent;
                           
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.$data.searching=false;
                        });                        
                    },
        
        //update the experiment list from server
        updateExperiments:function(response){
            app.$data.experiments = response.data.experiments;       
                            
            if(app.$data.experiments.length == 0)
            {
                app.$data.warningText = "No experiments found.";
            }
            else
            {
                app.$data.warningText = "";
            }

            app.$data.searchCount = app.$data.experiments.length;
        },

        //delete the selected experiment
        deleteExperiment:function(id){
            if(confirm("Delete Experiment?"))
            {
                app.$data.experiments=[];
                app.$data.warningText ='<i class="fas fa-spinner fa-spin"></i>';

                axios.post('/experimentSearch/', {
                        action :"deleteExperiment" ,
                        id:id,                                                                                                                             
                    })
                    .then(function (response) {   
                        if(response.data.status == "success")
                        {
                            app.$data.warningText ='The experiment "'+ response.data.title  +  '" was deleted.';
                        }  
                        else
                        {
                            app.$data.warningText="The experiment could not be deleted."
                        }

                        app.$data.experiments_recent = response.data.experiments_recent;
                                                                  
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.$data.searching=false;
                    });                        
                }
            }                          
    },

    mounted(){
        this.getRecentExperiments();       
        
        Vue.nextTick(() => {
            document.getElementById("idsearchInfo").focus();
        });
    },
}).mount('#app');
