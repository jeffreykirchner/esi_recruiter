"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

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
        sortByDate:function sortByDate(){

            app.dateSortButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            app.experiments.sort(function(a, b) {
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

            app.dateSortButtonText = 'Date <i class="fas fa-sort"></i>';
        },

        //sort by title
        sortByTitle:function sortByTitle(){

            app.titleSortButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            app.experiments.sort(function(a, b) {
                a=a.title.trim().toLowerCase();
                b=b.title.trim().toLowerCase();
                return a < b ? -1 : a > b ? 1 : 0;
            });

            app.titleSortButtonText = 'Title <i class="fas fa-sort"></i>';
        },

        //sort by manager
        sortByManager:function sortByManager(){

            app.managerSortButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            app.experiments.sort(function(a, b) {
                a=a.experiment_manager.trim().toLowerCase();
                b=b.experiment_manager.trim().toLowerCase();
                return a < b ? -1 : a > b ? 1 : 0;
            });

            app.managerSortButtonText = 'Manager <i class="fas fa-sort"></i>';
            },

        //get list of experiments based on search
        searchExperiments:function searchExperiments(){
            if(app.searchInfo == "")
                return;

            app.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.experiments=[];
            app.warningText = "";

            axios.post('/experimentSearch/', {
                            action :"searchExperiments" ,
                            searchInfo:app.searchInfo,                                                                                                                             
                        })
                        .then(function (response) {     
                            app.updateExperiments(response);
                            app.searchButtonText = 'Search <i class="fas fa-search"></i>';                                                   
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.searching=false;
                        });                        
        },
        
        //create new experient
        createExperiment:function createExperiment(){                    
            app.experiments = [];
            app.warningText = '';
            app.createExperimentButtonText ='<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experimentSearch/', {
                            action :"createExperiment" ,                                                                                                                                                                
                        })
                        .then(function (response) {     
                            app.updateExperiments(response);        
                            app.createExperimentButtonText = 'Create Experiment <i class="fas fa-plus"></i>';                                        
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.searching=false;
                        });                        
        },
        
        //get list of all experiments
        getAllExperiments:function getAllExperiments(){
            app.showAllButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.experiments = [];
            app.warningText = "";

            axios.post('/experimentSearch/', {
                            action :"getAllExperiments" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.updateExperiments(response);
                            app.showAllButtonText = 'Show All';
                           
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.searching=false;
                        });                        
                    },
        
        //get list of open experiments
        getOpenExperiments:function getOpenExperiments(){
            app.showOpenButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.experiments = [];
            app.warningText = "";

            axios.post('/experimentSearch/', {
                            action :"getOpenExperiments" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.updateExperiments(response);
                            app.showOpenButtonText = 'Show Open';
                           
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.searching=false;
                        });                        
                    },
        
        //get recent experiments
        getRecentExperiments:function getRecentExperiments(){
            
            axios.post('/experimentSearch/', {
                            action :"getRecentExperiments" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.experiments_recent = response.data.experiments_recent;
                           
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.searching=false;
                        });                        
                    },
        
        //update the experiment list from server
        updateExperiments:function updateExperiments(response){
            app.experiments = response.data.experiments;       
                            
            if(app.experiments.length == 0)
            {
                app.warningText = "No experiments found.";
            }
            else
            {
                app.warningText = "";
            }

            app.searchCount = app.experiments.length;
        },

        //delete the selected experiment
        deleteExperiment: async function deleteExperiment(id){
            if(await app.showConfirmDialog("Delete Experiment?"))
            {
                app.experiments=[];
                app.warningText ='<i class="fas fa-spinner fa-spin"></i>';

                axios.post('/experimentSearch/', {
                        action :"deleteExperiment" ,
                        id:id,                                                                                                                             
                    })
                    .then(function (response) {   
                        if(response.data.status == "success")
                        {
                            app.warningText ='The experiment "'+ response.data.title  +  '" was deleted.';
                        }  
                        else
                        {
                            app.warningText="The experiment could not be deleted."
                        }

                        app.experiments_recent = response.data.experiments_recent;
                                                                  
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.searching=false;
                    });                        
            }
        },
        
        {%include "modals/alert_dialog.js"%} 
    },

    mounted(){
        
        Vue.nextTick(() => {
            app.getRecentExperiments();  
            document.getElementById("idsearchInfo").focus();
        });
    },
}).mount('#app');
