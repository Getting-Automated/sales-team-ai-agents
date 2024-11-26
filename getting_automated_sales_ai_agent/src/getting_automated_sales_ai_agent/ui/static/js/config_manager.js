// Weight calculation functions
function updateCompanyWeights() {
    const weights = {
        industry: parseInt($("#industryWeight").val()),
        size: parseInt($("#sizeWeight").val()),
        location: parseInt($("#locationWeight").val()),
        growth: parseInt($("#growthWeight").val())
    };
    
    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    const factor = 100 / total;
    
    // Update all weights proportionally
    $("#industryWeight").val(Math.round(weights.industry * factor));
    $("#sizeWeight").val(Math.round(weights.size * factor));
    $("#locationWeight").val(Math.round(weights.location * factor));
    $("#growthWeight").val(Math.round(weights.growth * factor));
    
    // Update displays
    $("#industryWeightValue").text(Math.round(weights.industry * factor) + "%");
    $("#sizeWeightValue").text(Math.round(weights.size * factor) + "%");
    $("#locationWeightValue").text(Math.round(weights.location * factor) + "%");
    $("#growthWeightValue").text(Math.round(weights.growth * factor) + "%");
}

function updateIndividualWeights() {
    const weights = {
        role: parseInt($("#roleWeight").val()),
        authority: parseInt($("#authorityWeight").val()),
        department: parseInt($("#departmentWeight").val()),
        skills: parseInt($("#skillsWeight").val())
    };
    
    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    const factor = 100 / total;
    
    // Update all weights proportionally
    $("#roleWeight").val(Math.round(weights.role * factor));
    $("#authorityWeight").val(Math.round(weights.authority * factor));
    $("#departmentWeight").val(Math.round(weights.department * factor));
    $("#skillsWeight").val(Math.round(weights.skills * factor));
    
    // Update displays
    $("#roleWeightValue").text(Math.round(weights.role * factor) + "%");
    $("#authorityWeightValue").text(Math.round(weights.authority * factor) + "%");
    $("#departmentWeightValue").text(Math.round(weights.department * factor) + "%");
    $("#skillsWeightValue").text(Math.round(weights.skills * factor) + "%");
}

function updateTechnicalWeights() {
    const weights = {
        techStack: parseInt($("#techStackWeight").val()),
        integration: parseInt($("#integrationWeight").val()),
        infrastructure: parseInt($("#infrastructureWeight").val())
    };
    
    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    const factor = 100 / total;
    
    // Update all weights proportionally
    $("#techStackWeight").val(Math.round(weights.techStack * factor));
    $("#integrationWeight").val(Math.round(weights.integration * factor));
    $("#infrastructureWeight").val(Math.round(weights.infrastructure * factor));
    
    // Update displays
    $("#techStackWeightValue").text(Math.round(weights.techStack * factor) + "%");
    $("#integrationWeightValue").text(Math.round(weights.integration * factor) + "%");
    $("#infrastructureWeightValue").text(Math.round(weights.infrastructure * factor) + "%");
}

function updateOverallWeights() {
    const weights = {
        company: parseInt($("#companyWeight").val()),
        individual: parseInt($("#individualWeight").val()),
        technical: parseInt($("#technicalWeight").val()),
        market: parseInt($("#marketWeight").val())
    };
    
    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    const factor = 100 / total;
    
    // Update all weights proportionally
    $("#companyWeight").val(Math.round(weights.company * factor));
    $("#individualWeight").val(Math.round(weights.individual * factor));
    $("#technicalWeight").val(Math.round(weights.technical * factor));
    $("#marketWeight").val(Math.round(weights.market * factor));
    
    // Update displays
    $("#companyWeightValue").text(Math.round(weights.company * factor) + "%");
    $("#individualWeightValue").text(Math.round(weights.individual * factor) + "%");
    $("#technicalWeightValue").text(Math.round(weights.technical * factor) + "%");
    $("#marketWeightValue").text(Math.round(weights.market * factor) + "%");
}

// Tag management functions
function addTag(inputId, tagsId, type) {
    const input = $(`#${inputId}`);
    const value = input.val().trim();
    
    if (value) {
        const tagHtml = `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2 mb-2">
                ${value}
                <button onclick="removeTag(this)" class="ml-1 text-blue-400 hover:text-blue-600">&times;</button>
            </span>
        `;
        $(`#${tagsId}`).append(tagHtml);
        input.val('');
    }
}

function removeTag(button) {
    $(button).parent().remove();
}

function getTags(type) {
    const tags = [];
    $(`#${type}Tags span`).each(function() {
        tags.push($(this).contents().first().text().trim());
    });
    return tags;
}

// Configuration management
function getConfiguration() {
    return {
        customer_icp: {
            profile_overview: $("#targetOverview").val(),
            weights: {
                company: {
                    industry: parseInt($("#industryWeight").val()),
                    size: parseInt($("#sizeWeight").val()),
                    location: parseInt($("#locationWeight").val()),
                    growth: parseInt($("#growthWeight").val())
                },
                individual: {
                    role: parseInt($("#roleWeight").val()),
                    authority: parseInt($("#authorityWeight").val()),
                    department: parseInt($("#departmentWeight").val()),
                    skills: parseInt($("#skillsWeight").val())
                },
                technical: {
                    tech_stack: parseInt($("#techStackWeight").val()),
                    integration: parseInt($("#integrationWeight").val()),
                    infrastructure: parseInt($("#infrastructureWeight").val())
                },
                overall: {
                    company: parseInt($("#companyWeight").val()),
                    individual: parseInt($("#individualWeight").val()),
                    technical: parseInt($("#technicalWeight").val()),
                    market: parseInt($("#marketWeight").val())
                }
            },
            tags: {
                industries: getTags('industry'),
                business_models: getTags('businessModel'),
                technologies: getTags('technology'),
                locations: getTags('location'),
                growth_stages: getTags('growthStage')
            },
            target_departments: getTags('department'),
            job_titles: getTags('jobTitle'),
            decision_making_authority: getTags('authority'),
            required_skills: getTags('skill'),
            negative_criteria: getTags('negative'),
            minimum_requirements: {
                employee_count_min: parseInt($("#minEmployees").val()) || 0,
                employee_count_max: parseInt($("#maxEmployees").val()) || 999999
            }
        }
    };
}

function loadConfiguration(config) {
    if (!config || !config.customer_icp) return;
    
    const icp = config.customer_icp;
    
    // Load text fields
    $("#targetOverview").val(icp.profile_overview || '');
    $("#minEmployees").val(icp.minimum_requirements?.employee_count_min || '');
    $("#maxEmployees").val(icp.minimum_requirements?.employee_count_max || '');
    
    // Load weights
    if (icp.weights) {
        const weights = icp.weights;
        // Company weights
        if (weights.company) {
            $("#industryWeight").val(weights.company.industry || 25);
            $("#sizeWeight").val(weights.company.size || 25);
            $("#locationWeight").val(weights.company.location || 25);
            $("#growthWeight").val(weights.company.growth || 25);
            updateCompanyWeights();
        }
        
        // Individual weights
        if (weights.individual) {
            $("#roleWeight").val(weights.individual.role || 30);
            $("#authorityWeight").val(weights.individual.authority || 30);
            $("#departmentWeight").val(weights.individual.department || 20);
            $("#skillsWeight").val(weights.individual.skills || 20);
            updateIndividualWeights();
        }
        
        // Technical weights
        if (weights.technical) {
            $("#techStackWeight").val(weights.technical.tech_stack || 40);
            $("#integrationWeight").val(weights.technical.integration || 30);
            $("#infrastructureWeight").val(weights.technical.infrastructure || 30);
            updateTechnicalWeights();
        }
        
        // Overall weights
        if (weights.overall) {
            $("#companyWeight").val(weights.overall.company || 30);
            $("#individualWeight").val(weights.overall.individual || 30);
            $("#technicalWeight").val(weights.overall.technical || 20);
            $("#marketWeight").val(weights.overall.market || 20);
            updateOverallWeights();
        }
    }
    
    // Load tags
    function loadTags(tags, type) {
        if (!tags) return;
        $(`#${type}Tags`).empty();
        tags.forEach(tag => {
            const tagHtml = `
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2 mb-2">
                    ${tag}
                    <button onclick="removeTag(this)" class="ml-1 text-blue-400 hover:text-blue-600">&times;</button>
                </span>
            `;
            $(`#${type}Tags`).append(tagHtml);
        });
    }
    
    if (icp.tags) {
        loadTags(icp.tags.industries, 'industry');
        loadTags(icp.tags.business_models, 'businessModel');
        loadTags(icp.tags.technologies, 'technology');
        loadTags(icp.tags.locations, 'location');
        loadTags(icp.tags.growth_stages, 'growthStage');
    }
    
    loadTags(icp.target_departments, 'department');
    loadTags(icp.job_titles, 'jobTitle');
    loadTags(icp.decision_making_authority, 'authority');
    loadTags(icp.required_skills, 'skill');
    loadTags(icp.negative_criteria, 'negative');
}

// Initialize everything when document is ready
$(document).ready(function() {
    // Initialize weight sliders
    updateCompanyWeights();
    updateIndividualWeights();
    updateTechnicalWeights();
    updateOverallWeights();
    
    // Add event listeners for weight changes
    $("#industryWeight, #sizeWeight, #locationWeight, #growthWeight").on('input', updateCompanyWeights);
    $("#roleWeight, #authorityWeight, #departmentWeight, #skillsWeight").on('input', updateIndividualWeights);
    $("#techStackWeight, #integrationWeight, #infrastructureWeight").on('input', updateTechnicalWeights);
    $("#companyWeight, #individualWeight, #technicalWeight, #marketWeight").on('input', updateOverallWeights);
    
    // Initialize autocomplete for all input fields
    const inputMappings = {
        'industryInput': suggestions.industries,
        'businessModelInput': suggestions.businessModel,
        'technologyInput': suggestions.technologies,
        'locationInput': suggestions.locations,
        'growthStageInput': suggestions.growthStages,
        'departmentInput': suggestions.departments,
        'jobTitleInput': suggestions.jobTitles,
        'authorityInput': suggestions.authority,
        'skillInput': suggestions.skills,
        'negativeInput': suggestions.negativeCriteria
    };
    
    Object.entries(inputMappings).forEach(([inputId, suggestionList]) => {
        $(`#${inputId}`).autocomplete({
            source: suggestionList,
            minLength: 0
        }).on('focus', function() {
            $(this).autocomplete("search", "");
        });
    });
});
