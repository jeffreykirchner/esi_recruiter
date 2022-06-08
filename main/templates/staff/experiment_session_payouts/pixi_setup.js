{% load static %}

/**
 * update the pixi players with new info
 */
setupPixi(){    
    if(app.$data.payGroup!="consent") return;
    if(!app.$data.consentForm) return;
    if(!app.$data.consentForm.signature_required) return;

    app.$data.pixi_signature_texture = PIXI.Texture.from('{% static "signature_4.png" %}');

    for(let i=0;i<app.$data.sessionDayUsers.length;i++)
    {
        // if(app.$data.sessionDayUsers[i].pixi_app)
        // {
        //     app.$data.sessionDayUsers[i].pixi_app.destroy();
        // }
        
        app.$data.sessionDayUsers[i].pixi_app = app.resetPixiApp("signature_canvas_id_" + app.$data.sessionDayUsers[i].id, 
                                                                 app.$data.sessionDayUsers[i].profile_consent_form.signature_points,
                                                                 app.$data.sessionDayUsers[i].profile_consent_form.singnature_resolution)
    }
},

resetPixiApp(canvas_id, signature_points, signature_scale){
    
    let canvas = document.getElementById(canvas_id);

    let pixi_app = new PIXI.Application({resizeTo : canvas,
                                    backgroundColor : 0xFFFFFF,
                                    autoResize: true,
                                    antialias: true,
                                    resolution: 1,
                                    view: canvas });
    
    for (let i in signature_points) {

        let t = signature_points[i];        

        let points = [];

        for(let j=0;j<t.length;j++)
        {
            points.push(new PIXI.Point(t[j].x,
                                       t[j].y))
        }
            
        r = new PIXI.SimpleRope(app.$data.pixi_signature_texture, points);

        r.scale.x = r.scale.y = canvas.height / signature_scale.height;

        pixi_app.stage.addChild(r);
    }

    pixi_app.destroy();
},

//load past signature
clearPixi(pixi_app,canvas_id){

    // let canvas = document.getElementById(canvas_id);

    // let background = new PIXI.Graphics();
    // background.beginFill(0xffffff);
    // background.drawRect(0, 0, canvas.width, canvas.height);
    // background.endFill();

    pixi_app.stage.removeChildren();
},

