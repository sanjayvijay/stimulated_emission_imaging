// Figure 2 interactively loads static images, stored locally
function update_figure_2() {
  var sample_type = document.getElementById("Figure_2_sample_type").value;
  var imaging_modality = document.getElementById("Figure_2_imaging_modality").value;
  var filename = "./images/figure_2/" + sample_type + "_" + imaging_modality + ".svg";
  var image = document.getElementById("Figure_2_image");
  image.src = filename;
}




// Figure 5 interactively loads static images, stored locally
function update_figure_5() {
  var z = document.getElementById("Figure_5_z").value;
  var filename = "./images/figure_5/darkfield_STE_image_" + z + ".svg";
  var image = document.getElementById("Figure_5_image");
  image.src = filename;
}

// Figure 6 interactively loads static images, stored locally
function update_figure_6() {
  var z = document.getElementById("Figure_6_z").value;
  var filename = "./images/figure_6/fluorescence_depletion_image_" + z + ".svg";
  var image = document.getElementById("Figure_6_image");
  image.src = filename;
}

// Figure 7 interactively loads static images, stored locally
function update_figure_7() {
  var angle = document.getElementById("Figure_7_angle").value;
  var filename = "./images/figure_7/phase_STE_image_" + angle + ".svg";
  var image = document.getElementById("Figure_7_image");
  image.src = filename;
}
